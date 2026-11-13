"""Guardrailed natural-language analytics compiler over a curated semantic layer."""
from dataclasses import dataclass
from datetime import date
import re
import sqlite3

class UnsupportedQuery(ValueError):pass

DIMENSIONS={'region':'region','product':'product','channel':'channel','day':'order_date'}
METRICS={'revenue':('SUM(amount_cents)','revenue_cents'),
         'orders':('COUNT(*)','order_count'),
         'average order':('AVG(amount_cents)','average_cents')}

@dataclass(frozen=True)
class Query:
    sql:str
    params:tuple
    metric:str
    dimension:str|None

class SemanticPlanner:
    def compile(self,utterance,*,limit=20):
        if not isinstance(utterance,str) or not 1<=limit<=100:raise UnsupportedQuery('invalid question')
        normalized=' '.join(utterance.lower().split())
        # No free-form SQL / DDL: only recognized metric and filter phrases.
        if any(re.search(r'\b'+word+r'\b',normalized) for word in ('drop','delete','update','insert','alter','union','pragma','attach')):
            raise UnsupportedQuery('unsafe operation')
        metrics=[m for m in METRICS if re.search(r'\b'+re.escape(m)+r'\b',normalized)]
        if len(metrics)!=1:raise UnsupportedQuery('specify exactly one recognized metric')
        metric=metrics[0];dimension=None
        for phrase,col in DIMENSIONS.items():
            if re.search(r'\b(?:by|per) '+phrase+r'\b',normalized):
                if dimension is not None:raise UnsupportedQuery('one grouping dimension supported')
                dimension=col
        where=[];params=[]
        for field in ('region','product','channel'):
            match=re.search(r'\bin '+field+r' ([a-z0-9_-]+)\b',normalized)
            if match:
                where.append(field+' = ?');params.append(match.group(1))
        date_from=re.search(r'\bfrom (\d{4}-\d{2}-\d{2})\b',normalized)
        date_to=re.search(r'\bto (\d{4}-\d{2}-\d{2})\b',normalized)
        for match,operator in ((date_from,'>='),(date_to,'<=')):
            if match:
                try:date.fromisoformat(match.group(1))
                except ValueError as e:raise UnsupportedQuery('bad date') from e
                where.append('order_date '+operator+' ?');params.append(match.group(1))
        aggregate,alias=METRICS[metric]
        cols=f'{dimension} AS dimension, {aggregate} AS {alias}' if dimension else f'{aggregate} AS {alias}'
        sql=f'SELECT {cols} FROM orders'
        if where:sql+=' WHERE '+' AND '.join(where)
        if dimension:sql+=f' GROUP BY {dimension} ORDER BY {alias} DESC'
        sql+=' LIMIT ?';params.append(limit)
        return Query(sql,tuple(params),metric,dimension)

class AnalyticsEngine:
    def __init__(self,db):self.db=db;self.planner=SemanticPlanner()
    def execute(self,question,limit=20):
        plan=self.planner.compile(question,limit=limit)
        cur=self.db.execute(plan.sql,plan.params)
        rows=[dict(zip([x[0] for x in cur.description],row)) for row in cur.fetchall()]
        return {'query':plan.sql,'parameters':plan.params,'rows':rows,'semantic_metric':plan.metric}

def demo_database():
    db=sqlite3.connect(':memory:');db.executescript("""
    CREATE TABLE orders(order_id TEXT PRIMARY KEY,order_date TEXT NOT NULL,region TEXT NOT NULL,
       product TEXT NOT NULL,channel TEXT NOT NULL,amount_cents INTEGER NOT NULL);
    INSERT INTO orders VALUES ('1','2026-01-01','west','shoes','online',1500),
      ('2','2026-01-02','east','shoes','store',2000),('3','2026-02-01','west','hats','online',750);
    """);return db
if __name__=='__main__':print(AnalyticsEngine(demo_database()).execute('revenue by region'))
