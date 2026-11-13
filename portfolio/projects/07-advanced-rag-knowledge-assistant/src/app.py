"""Auditable offline RAG: scoped retrieval, hybrid ranking, cited generation interface."""
from dataclasses import dataclass
from collections import Counter,defaultdict
import hashlib
import json
import math
import re

TOKENS=re.compile(r'[\w-]+',re.UNICODE)
def tokenize(text):return [x.lower() for x in TOKENS.findall(text)]

@dataclass(frozen=True)
class Chunk:
    id:str
    doc_id:str
    tenant:str
    text:str
    source:str
    offset:int

class Index:
    def __init__(self):self.chunks={};self.term_counts={};self.df=Counter()
    def add(self,doc_id,text,*,tenant,source,max_words=90,overlap=20):
        if not (0<=overlap<max_words) or not tenant or not doc_id:raise ValueError('invalid index settings')
        words=text.split()
        step=max_words-overlap
        for start in range(0,len(words),step):
            snippet=' '.join(words[start:start+max_words]);fingerprint=hashlib.sha256((tenant+doc_id+str(start)+snippet).encode()).hexdigest()[:20]
            chunk=Chunk(fingerprint,doc_id,tenant,snippet,source,start)
            if chunk.id in self.chunks:continue
            counter=Counter(tokenize(snippet));self.chunks[fingerprint]=chunk;self.term_counts[fingerprint]=counter
            self.df.update(counter.keys())
            if start+max_words>=len(words):break
    def search(self,query,*,tenant,top_k=5,allowed_sources=None):
        if not tenant or not 1<=top_k<=50:raise ValueError('invalid query scope')
        terms=tokenize(query)[:30]
        if not terms:return []
        candidates=[c for c in self.chunks.values() if c.tenant==tenant and
                    (allowed_sources is None or c.source in allowed_sources)]
        if not candidates:return []
        avg_len=sum(sum(self.term_counts[c.id].values()) for c in candidates)/len(candidates)
        ranked=[]
        for c in candidates:
            counts=self.term_counts[c.id];length=sum(counts.values());score=0.0
            for term in terms:
                if not counts[term]:continue
                # Tenant-local document frequency avoids cross-tenant influence.
                df=sum(term in self.term_counts[v.id] for v in candidates)
                idf=math.log(1+(len(candidates)-df+.5)/(df+.5))
                score+=idf*counts[term]*2.2/(counts[term]+1.2*(.25+.75*length/avg_len))
            if score>0:ranked.append((score,c))
        ranked.sort(key=lambda x:(-x[0],x[1].id))
        return [dict(id=c.id,doc_id=c.doc_id,source=c.source,score=round(score,5),excerpt=c.text)
                for score,c in ranked[:top_k]]

class GroundedAssistant:
    """Generator adapter receives untrusted, cited excerpts; validation is deterministic."""
    def __init__(self,index,generator=None):self.index=index;self.generator=generator
    def answer(self,question,*,tenant,sources=None):
        hits=self.index.search(question,tenant=tenant,allowed_sources=sources)
        if not hits:return {'answer':'Insufficient evidence in permitted documents.','citations':[],'grounded':False}
        context=[{'id':h['id'],'source':h['source'],'excerpt':h['excerpt']} for h in hits]
        if self.generator:
            # Caller must configure a vetted provider. Retrieval content is DATA, never instructions.
            draft=self.generator(question,context)
            ids={h['id'] for h in hits}
            if not isinstance(draft,dict) or not isinstance(draft.get('answer'),str) or not isinstance(draft.get('citations'),list):
                raise ValueError('invalid generator result')
            if not draft['citations'] or any(cid not in ids for cid in draft['citations']):
                raise ValueError('answer lacks verifiable source IDs')
            return {**draft,'grounded':True}
        return {'answer':'Relevant source excerpts are available below. No unsupported synthesis was generated.',
                'citations':[h['id'] for h in hits],'excerpts':context,'grounded':False}

def retrieval_recall_at_k(index,questions,*,tenant,k=5):
    if not questions:raise ValueError('empty evaluation set')
    correct=0
    for question,expected_doc in questions:
        hits=index.search(question,tenant=tenant,top_k=k)
        correct+=any(h['doc_id']==expected_doc for h in hits)
    return correct/len(questions)

if __name__=='__main__':
    i=Index();i.add('runbook','Restart the queue worker after the alarm clears',tenant='demo',source='runbook.md')
    print(json.dumps(GroundedAssistant(i).answer('queue worker alarm',tenant='demo'),indent=2))
