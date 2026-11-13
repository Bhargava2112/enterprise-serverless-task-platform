"""Transactional bronze/silver/gold incremental lakehouse reference on SQLite."""
import hashlib
import json
import sqlite3
from datetime import datetime,timezone

class QualityError(ValueError):pass
class Lakehouse:
    def __init__(self,filename=':memory:'):
        self.db=sqlite3.connect(filename,isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS bronze(event_id TEXT PRIMARY KEY,payload TEXT NOT NULL,sha256 TEXT NOT NULL,ingested_utc TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS silver(event_id TEXT PRIMARY KEY,customer_id TEXT NOT NULL,amount_cents INTEGER NOT NULL,occurred_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS rejected(event_id TEXT PRIMARY KEY,reason TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS dim_customer(customer_id TEXT NOT NULL,segment TEXT NOT NULL,valid_from INTEGER NOT NULL,valid_to INTEGER,PRIMARY KEY(customer_id,valid_from));
        CREATE TABLE IF NOT EXISTS lineage(run_id TEXT PRIMARY KEY,source_count INTEGER NOT NULL,accepted INTEGER NOT NULL,rejected INTEGER NOT NULL,sha256 TEXT NOT NULL);
        """)
    def ingest(self,records,run_id):
        """Idempotent replay, atomic processing, and explicit rejection quarantine."""
        records=list(records);self.db.execute('BEGIN IMMEDIATE')
        try:
            canonical=json.dumps(records,sort_keys=True,default=str).encode();digest=hashlib.sha256(canonical).hexdigest()
            row=self.db.execute('SELECT sha256 FROM lineage WHERE run_id=?',(run_id,)).fetchone()
            if row:
                if row[0]!=digest:raise QualityError('run id already used for different data')
                self.db.execute('COMMIT');return {'replay':True}
            accepted=rejects=0
            for rec in records:
                eid=rec.get('event_id') if isinstance(rec,dict) else None
                if not isinstance(eid,str) or not eid.strip():raise QualityError('record has no stable event_id')
                data=json.dumps(rec,sort_keys=True);sha=hashlib.sha256(data.encode()).hexdigest()
                self.db.execute('INSERT OR IGNORE INTO bronze VALUES(?,?,?,?)',
                    (eid,data,sha,datetime.now(timezone.utc).isoformat()))
                try:
                    customer=rec['customer_id'];amount=rec['amount_cents'];ts=rec['occurred_at']
                    if not isinstance(customer,str) or not customer or type(amount)!=int or amount<0:raise ValueError()
                    datetime.fromisoformat(ts.replace('Z','+00:00'))
                    self.db.execute('INSERT OR IGNORE INTO silver VALUES(?,?,?,?)',(eid,customer,amount,ts))
                    accepted+=1
                except (ValueError,KeyError,TypeError,AttributeError):
                    self.db.execute('INSERT OR IGNORE INTO rejected VALUES(?,?)',(eid,'invalid customer/amount/time'))
                    rejects+=1
            self.db.execute('INSERT INTO lineage VALUES(?,?,?,?,?)',(run_id,len(records),accepted,rejects,digest))
            self.db.execute('COMMIT')
            return {'replay':False,'accepted':accepted,'rejected':rejects,'sha256':digest}
        except Exception:self.db.execute('ROLLBACK');raise
    def upsert_customer(self,customer,segment,effective_at):
        if not customer or not segment or not isinstance(effective_at,int):raise ValueError('invalid dimension data')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            current=self.db.execute('SELECT segment,valid_from FROM dim_customer WHERE customer_id=? AND valid_to IS NULL',(customer,)).fetchone()
            if current and current[0]==segment:self.db.execute('COMMIT');return False
            if current:
                if effective_at<=current[1]:raise ValueError('effective_at must increase')
                self.db.execute('UPDATE dim_customer SET valid_to=? WHERE customer_id=? AND valid_to IS NULL',(effective_at,customer))
            self.db.execute('INSERT INTO dim_customer VALUES(?,?,?,NULL)',(customer,segment,effective_at))
            self.db.execute('COMMIT');return True
        except Exception:self.db.execute('ROLLBACK');raise
    def gold_revenue_by_customer(self):
        return self.db.execute('SELECT customer_id,COUNT(*),SUM(amount_cents) FROM silver GROUP BY customer_id ORDER BY customer_id').fetchall()
    def quality_metrics(self):
        return dict(bronze=self.db.execute('SELECT COUNT(*) FROM bronze').fetchone()[0],
                    silver=self.db.execute('SELECT COUNT(*) FROM silver').fetchone()[0],
                    rejected=self.db.execute('SELECT COUNT(*) FROM rejected').fetchone()[0])
if __name__=='__main__':
    lake=Lakehouse();print(lake.ingest([{'event_id':'e1','customer_id':'c1','amount_cents':900,'occurred_at':'2026-01-01T00:00:00Z'}],'load-1'))
