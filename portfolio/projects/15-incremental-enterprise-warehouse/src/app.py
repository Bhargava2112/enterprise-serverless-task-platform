"""Incremental facts and SCD2 dimensions with transactional quality gates."""
from datetime import datetime
import hashlib
import json
import sqlite3

class WarehouseError(ValueError):pass

class Warehouse:
    def __init__(self,filename=':memory:'):
        self.db=sqlite3.connect(filename,isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS dim_product(sk INTEGER PRIMARY KEY AUTOINCREMENT,
            natural_key TEXT NOT NULL, category TEXT NOT NULL,valid_from TEXT NOT NULL,
            valid_to TEXT, UNIQUE(natural_key,valid_from));
        CREATE TABLE IF NOT EXISTS fact_sales(event_id TEXT PRIMARY KEY,product_sk INTEGER NOT NULL,
            amount_cents INTEGER NOT NULL CHECK(amount_cents>=0),sale_date TEXT NOT NULL,
            FOREIGN KEY(product_sk) REFERENCES dim_product(sk));
        CREATE TABLE IF NOT EXISTS checkpoints(batch_id TEXT PRIMARY KEY,hash TEXT NOT NULL,processed INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS quarantine(event_id TEXT PRIMARY KEY,reason TEXT NOT NULL);
        """)
    def product_version(self,key,category,effective_from):
        if not key or not category:raise WarehouseError('invalid product')
        datetime.fromisoformat(effective_from)
        row=self.db.execute('SELECT sk,category,valid_from FROM dim_product WHERE natural_key=? AND valid_to IS NULL',(key,)).fetchone()
        if row and row[1]==category:return row[0]
        if row:
            if effective_from<=row[2]:raise WarehouseError('effective date must increase')
            self.db.execute('UPDATE dim_product SET valid_to=? WHERE sk=?',(effective_from,row[0]))
        cur=self.db.execute('INSERT INTO dim_product(natural_key,category,valid_from) VALUES(?,?,?)',(key,category,effective_from))
        return cur.lastrowid
    def load_sales(self,batch_id,events,products):
        """Products are SCD2 changes [key, category, effective_at]; events carry event-time."""
        events=list(events);products=list(products)
        digest=hashlib.sha256(json.dumps({'events':events,'products':products},sort_keys=True).encode()).hexdigest()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            old=self.db.execute('SELECT hash FROM checkpoints WHERE batch_id=?',(batch_id,)).fetchone()
            if old:
                if old[0]!=digest:raise WarehouseError('batch_id payload conflict')
                self.db.execute('COMMIT');return {'replay':True}
            for key,cat,when in products:self.product_version(key,cat,when)
            accepted=rejected=0
            for e in events:
                try:
                    eid=e['event_id'];key=e['product_id'];value=e['amount_cents'];when=e['sale_date']
                    datetime.fromisoformat(when)
                    if not eid or type(value)!=int or value<0:raise ValueError()
                    row=self.db.execute("""SELECT sk FROM dim_product WHERE natural_key=? AND valid_from<=?
                      AND (valid_to IS NULL OR valid_to>?) ORDER BY valid_from DESC LIMIT 1""",(key,when,when)).fetchone()
                    if not row:raise LookupError('unmapped dimension')
                    cur=self.db.execute('INSERT OR IGNORE INTO fact_sales VALUES(?,?,?,?)',(eid,row[0],value,when))
                    accepted+=cur.rowcount
                except (KeyError,ValueError,TypeError,LookupError) as err:
                    eid=e.get('event_id') if isinstance(e,dict) else None
                    if not eid:raise WarehouseError('missing immutable event_id') from err
                    self.db.execute('INSERT OR IGNORE INTO quarantine VALUES(?,?)',(eid,'invalid fact or unknown dimension'))
                    rejected+=1
            self.db.execute('INSERT INTO checkpoints VALUES(?,?,?)',(batch_id,digest,accepted))
            self.db.execute('COMMIT');return {'replay':False,'accepted':accepted,'quarantined':rejected}
        except Exception:self.db.execute('ROLLBACK');raise
    def category_revenue(self):
        return self.db.execute("""SELECT p.category,COUNT(*),SUM(f.amount_cents)
           FROM fact_sales f JOIN dim_product p ON f.product_sk=p.sk
           GROUP BY p.category ORDER BY p.category""").fetchall()
    def reconcile(self):
        return {'facts':self.db.execute('SELECT COUNT(*) FROM fact_sales').fetchone()[0],
                'quarantined':self.db.execute('SELECT COUNT(*) FROM quarantine').fetchone()[0],
                'revenue_cents':self.db.execute('SELECT COALESCE(SUM(amount_cents),0) FROM fact_sales').fetchone()[0]}

if __name__=='__main__':
    w=Warehouse();print(w.load_sales('b1',[{'event_id':'e1','product_id':'p1','amount_cents':990,'sale_date':'2026-01-03'}],[('p1','electronics','2026-01-01')]))
