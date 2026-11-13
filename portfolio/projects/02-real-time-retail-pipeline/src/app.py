"""Exactly-once-at-the-projection retail event consumer with transactional outbox."""
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import defaultdict
import json
import sqlite3
import uuid

class OutOfOrder(ValueError): pass
class InsufficientStock(ValueError): pass

@dataclass(frozen=True)
class Event:
    event_id: str
    order_id: str
    sequence: int
    kind: str
    sku: str
    quantity: int
    unit_cents: int
    occurred_at: str

    @classmethod
    def new(cls, order_id, sequence, kind, sku, quantity, unit_cents=0):
        if kind not in {'RESTOCK','PURCHASE','REFUND'} or quantity <= 0 or sequence <= 0:
            raise ValueError('invalid event')
        if not sku or unit_cents < 0:
            raise ValueError('invalid SKU/price')
        return cls(str(uuid.uuid4()),order_id,sequence,kind,sku,quantity,unit_cents,
                   datetime.now(timezone.utc).isoformat())

class RetailStore:
    """SQLite reference adapter; replace outbox poller with Kafka in deployment."""
    def __init__(self, filename=':memory:'):
        self.db=sqlite3.connect(filename, isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript("""
         CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY, payload TEXT NOT NULL, dispatched INTEGER NOT NULL DEFAULT 0);
         CREATE TABLE IF NOT EXISTS seen(event_id TEXT PRIMARY KEY);
         CREATE TABLE IF NOT EXISTS order_versions(order_id TEXT PRIMARY KEY, version INTEGER NOT NULL);
         CREATE TABLE IF NOT EXISTS stock(sku TEXT PRIMARY KEY, units INTEGER NOT NULL CHECK(units>=0));
         CREATE TABLE IF NOT EXISTS sales(event_id TEXT PRIMARY KEY, sku TEXT NOT NULL, units INTEGER NOT NULL,
           cents INTEGER NOT NULL, occurred_at TEXT NOT NULL);
        """)
    def enqueue(self,event):
        if not isinstance(event, Event): raise TypeError('Event required')
        with self.db:
            self.db.execute('INSERT INTO outbox(id,payload) VALUES(?,?)',
                (event.event_id,json.dumps(event.__dict__,sort_keys=True)))
    def pending(self,limit=100):
        if not 1<=limit<=1000: raise ValueError('invalid limit')
        return [Event(**json.loads(row[0])) for row in self.db.execute(
            'SELECT payload FROM outbox WHERE dispatched=0 ORDER BY rowid LIMIT ?', (limit,))]
    def apply(self,event):
        """Returns True if applied, False on duplicate. Atomic across projections and dedupe."""
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if self.db.execute('SELECT 1 FROM seen WHERE event_id=?',(event.event_id,)).fetchone():
                self.db.execute('COMMIT');return False
            prior=self.db.execute('SELECT version FROM order_versions WHERE order_id=?',(event.order_id,)).fetchone()
            expected=1 if prior is None else prior[0]+1
            if event.sequence!=expected:raise OutOfOrder(f'expected {expected}, got {event.sequence}')
            current=self.units(event.sku)
            delta=event.quantity if event.kind in ('RESTOCK','REFUND') else -event.quantity
            if current+delta<0:raise InsufficientStock(event.sku)
            self.db.execute('INSERT INTO stock(sku,units) VALUES(?,?) ON CONFLICT(sku) DO UPDATE SET units=excluded.units',
                            (event.sku,current+delta))
            if event.kind in ('PURCHASE','REFUND'):
                signed=1 if event.kind=='PURCHASE' else -1
                self.db.execute('INSERT INTO sales VALUES(?,?,?,?,?)',
                    (event.event_id,event.sku,signed*event.quantity,signed*event.quantity*event.unit_cents,event.occurred_at))
            self.db.execute('INSERT INTO seen(event_id) VALUES(?)',(event.event_id,))
            self.db.execute('INSERT INTO order_versions(order_id,version) VALUES(?,?) ON CONFLICT(order_id) DO UPDATE SET version=excluded.version',
                            (event.order_id,event.sequence))
            self.db.execute('COMMIT');return True
        except Exception:
            self.db.execute('ROLLBACK');raise
    def dispatch_once(self,publisher):
        """Publishing is at-least-once; the sink handles deduplication."""
        sent=0
        for ev in self.pending():
            publisher(ev)
            with self.db:self.db.execute('UPDATE outbox SET dispatched=1 WHERE id=?',(ev.event_id,))
            sent+=1
        return sent
    def units(self,sku):
        result=self.db.execute('SELECT units FROM stock WHERE sku=?',(sku,)).fetchone()
        return result[0] if result else 0
    def revenue(self):
        row=self.db.execute('SELECT COALESCE(SUM(cents),0) FROM sales').fetchone()
        return row[0]
    def close(self):self.db.close()

if __name__=='__main__':
    db=RetailStore();ev=Event.new('restock-1',1,'RESTOCK','SKU-101',100);db.enqueue(ev)
    db.dispatch_once(db.apply);print({'inventory':db.units('SKU-101'),'revenue_cents':db.revenue()})
