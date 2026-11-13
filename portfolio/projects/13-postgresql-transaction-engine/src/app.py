"""Double-entry funds ledger with idempotency and optimistic-account versions.

SQLite deterministic adapter for tests; PostgreSQL DDL in infra/postgresql.sql.
"""
import json
import sqlite3
import uuid
from decimal import Decimal,InvalidOperation

class Conflict(RuntimeError):pass
class InsufficientFunds(RuntimeError):pass

class Ledger:
    def __init__(self,filename=':memory:'):
        self.db=sqlite3.connect(filename,isolation_level=None,timeout=3)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA busy_timeout=3000')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY,cents INTEGER NOT NULL CHECK(cents>=0),version INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS transfers(id TEXT PRIMARY KEY,idem_key TEXT NOT NULL UNIQUE,from_id TEXT NOT NULL,to_id TEXT NOT NULL,cents INTEGER NOT NULL CHECK(cents>0),created_utc TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS entries(transfer_id TEXT NOT NULL,account_id TEXT NOT NULL,delta_cents INTEGER NOT NULL,
            PRIMARY KEY(transfer_id,account_id),FOREIGN KEY(transfer_id) REFERENCES transfers(id),
            FOREIGN KEY(account_id) REFERENCES accounts(id));
        """)
    def open_account(self,account_id,initial_cents=0):
        if not account_id or type(initial_cents)!=int or initial_cents<0:raise ValueError('invalid account')
        with self.db:self.db.execute('INSERT INTO accounts(id,cents) VALUES(?,?)',(account_id,initial_cents))
    def balance(self,account_id):
        result=self.db.execute('SELECT cents FROM accounts WHERE id=?',(account_id,)).fetchone()
        if result is None:raise KeyError(account_id)
        return result[0]
    def transfer(self,source,target,cents,idempotency_key):
        if source==target or not source or not target or type(cents)!=int or cents<=0 or not idempotency_key:
            raise ValueError('invalid transfer request')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            existing=self.db.execute('SELECT id,from_id,to_id,cents FROM transfers WHERE idem_key=?',(idempotency_key,)).fetchone()
            if existing:
                if (source,target,cents)!=existing[1:]:raise Conflict('idempotency key already used for different request')
                self.db.execute('COMMIT');return {'transfer_id':existing[0],'replay':True}
            src=self.db.execute('SELECT cents,version FROM accounts WHERE id=?',(source,)).fetchone()
            dst=self.db.execute('SELECT cents,version FROM accounts WHERE id=?',(target,)).fetchone()
            if not src or not dst:raise KeyError('account not found')
            if src[0]<cents:raise InsufficientFunds(source)
            tid=str(uuid.uuid4())
            updated=self.db.execute('UPDATE accounts SET cents=cents-?,version=version+1 WHERE id=? AND version=?',
                                    (cents,source,src[1]))
            if updated.rowcount!=1:raise Conflict('stale account version')
            updated=self.db.execute('UPDATE accounts SET cents=cents+?,version=version+1 WHERE id=? AND version=?',
                                    (cents,target,dst[1]))
            if updated.rowcount!=1:raise Conflict('stale account version')
            self.db.execute('INSERT INTO transfers(id,idem_key,from_id,to_id,cents) VALUES(?,?,?,?,?)',
                            (tid,idempotency_key,source,target,cents))
            self.db.executemany('INSERT INTO entries VALUES(?,?,?)',[(tid,source,-cents),(tid,target,cents)])
            self.db.execute('COMMIT')
            return {'transfer_id':tid,'replay':False}
        except Exception:self.db.execute('ROLLBACK');raise
    def verify(self):
        unbalanced=self.db.execute('SELECT transfer_id FROM entries GROUP BY transfer_id HAVING SUM(delta_cents)<>0').fetchall()
        missing=self.db.execute('SELECT id FROM transfers WHERE (SELECT COUNT(*) FROM entries WHERE transfer_id=transfers.id)<>2').fetchall()
        return {'valid':not(unbalanced or missing),'entries':self.db.execute('SELECT COUNT(*) FROM entries').fetchone()[0]}

if __name__=='__main__':
    ledger=Ledger();ledger.open_account('a',3000);ledger.open_account('b')
    print(ledger.transfer('a','b',250,'req-001'));print(ledger.verify())
