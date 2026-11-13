"""Durable change-log, checkpointed apply and deduplicated sink reference engine."""
import json
import sqlite3
from datetime import datetime,timezone

class OutOfSequence(ValueError):pass
class CDCSource:
    def __init__(self,filename=':memory:'):
        self.db=sqlite3.connect(filename,isolation_level=None)
        self.db.executescript("""
         CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL);
         CREATE TABLE IF NOT EXISTS changelog(seq INTEGER PRIMARY KEY AUTOINCREMENT,entity_id TEXT NOT NULL,
           operation TEXT NOT NULL,payload TEXT,version INTEGER NOT NULL);
        """)
    def change(self,entity_id,operation,payload=None):
        if not entity_id or operation not in ('UPSERT','DELETE') or (operation=='UPSERT' and not isinstance(payload,dict)):
            raise ValueError('invalid event')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            prior=self.db.execute('SELECT version FROM records WHERE id=?',(entity_id,)).fetchone()
            version=prior[0]+1 if prior else 1
            if operation=='UPSERT':
                encoded=json.dumps(payload,sort_keys=True)
                self.db.execute('INSERT INTO records VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,version=excluded.version',(entity_id,encoded,version))
            else:
                encoded=None
                self.db.execute('DELETE FROM records WHERE id=?',(entity_id,))
            self.db.execute('INSERT INTO changelog(entity_id,operation,payload,version) VALUES(?,?,?,?)',
                            (entity_id,operation,encoded,version))
            seq=self.db.execute('SELECT last_insert_rowid()').fetchone()[0]
            self.db.execute('COMMIT');return seq
        except Exception:self.db.execute('ROLLBACK');raise
    def poll(self,after=0,limit=100):
        if not 1<=limit<=1000:raise ValueError('invalid limit')
        return [dict(zip(('seq','entity_id','operation','payload','version'),row)) for row in
                self.db.execute('SELECT seq,entity_id,operation,payload,version FROM changelog WHERE seq>? ORDER BY seq LIMIT ?',
                                (after,limit))]

class CDCSink:
    def __init__(self,filename=':memory:'):
        self.db=sqlite3.connect(filename,isolation_level=None)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS replica(id TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS applied(seq INTEGER PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS checkpoint(stream TEXT PRIMARY KEY,last_seq INTEGER NOT NULL);
        """)
    def last_seq(self,stream):
        row=self.db.execute('SELECT last_seq FROM checkpoint WHERE stream=?',(stream,)).fetchone()
        return row[0] if row else 0
    def apply_batch(self,stream,events):
        """Source offsets and record changes commit as a single sink transaction."""
        if not stream:raise ValueError('missing stream')
        events=list(events);self.db.execute('BEGIN IMMEDIATE')
        try:
            last=self.last_seq(stream)
            applied=0
            for event in events:
                seq=event['seq']
                if seq<=last:continue
                if seq!=last+1:raise OutOfSequence(f'missing source offset {last+1}')
                if event['operation']=='UPSERT':
                    obj=json.loads(event['payload'])
                    self.db.execute('INSERT INTO replica VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,version=excluded.version',
                                    (event['entity_id'],json.dumps(obj,sort_keys=True),event['version']))
                elif event['operation']=='DELETE':
                    self.db.execute('DELETE FROM replica WHERE id=?',(event['entity_id'],))
                else:raise ValueError('unknown operation')
                self.db.execute('INSERT OR IGNORE INTO applied(seq) VALUES(?)',(seq,))
                last=seq;applied+=1
            self.db.execute('INSERT INTO checkpoint VALUES(?,?) ON CONFLICT(stream) DO UPDATE SET last_seq=excluded.last_seq',(stream,last))
            self.db.execute('COMMIT');return applied
        except Exception:self.db.execute('ROLLBACK');raise
    def snapshot(self):
        return {row[0]:json.loads(row[1]) for row in self.db.execute('SELECT id,payload FROM replica ORDER BY id')}

def replicate_once(source,sink,stream='orders',limit=100):
    return sink.apply_batch(stream,source.poll(sink.last_seq(stream),limit))

if __name__=='__main__':
    a=CDCSource();b=CDCSink();a.change('user1','UPSERT',{'tier':'gold'})
    print(replicate_once(a,b),b.snapshot())
