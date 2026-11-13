"""Inspectable feature-based quality classification for greyscale line images."""
from dataclasses import dataclass
import json
import math

class ImageError(ValueError):pass

def features(pixels):
    """Return mean luminance, edge density, dark-defect fraction and largest dark cluster."""
    if not pixels or not isinstance(pixels,list) or not pixels[0]:raise ImageError('empty image')
    width=len(pixels[0]);height=len(pixels)
    if width*height>4_000_000 or any(len(row)!=width for row in pixels):raise ImageError('invalid dimensions')
    for row in pixels:
        for p in row:
            if type(p)!=int or not 0<=p<=255:raise ImageError('invalid pixel')
    mean=sum(sum(r) for r in pixels)/(width*height)/255
    dark={(r,c) for r in range(height) for c in range(width) if pixels[r][c]<70}
    edges=sum(abs(pixels[r][c]-pixels[r][c-1]) for r in range(height) for c in range(1,width))
    edges+=sum(abs(pixels[r][c]-pixels[r-1][c]) for r in range(1,height) for c in range(width))
    edge_density=edges/max(1,(width-1)*height+(height-1)*width)/255
    largest=0
    while dark:
        stack=[dark.pop()];size=0
        while stack:
            r,c=stack.pop();size+=1
            for candidate in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if candidate in dark:dark.remove(candidate);stack.append(candidate)
        largest=max(largest,size)
    return (mean,edge_density,largest/(width*height),
            sum(p<70 for row in pixels for p in row)/(width*height))

def sigmoid(x):return 1/(1+math.exp(-max(-60,min(60,x))))

class VisualInspector:
    """Trainable logistic inspection head on interpretable image features.

    Intended as offline baseline, NOT a deployed deep-learning quality system.
    """
    def __init__(self,threshold=.65):
        if not 0<threshold<1:raise ValueError('bad threshold')
        self.threshold=threshold;self.weights=[0.]*5;self.fitted=False
    def fit(self,labeled_images,epochs=500):
        data=[(features(p),int(y)) for p,y in labeled_images]
        if len(data)<6 or set(y for _,y in data)!={0,1}:raise ValueError('need both classes and 6+ samples')
        weights=[0.]*5
        for _ in range(epochs):
            gradients=[0.]*5
            for x,y in data:
                row=(1.,)+x;err=sigmoid(sum(a*b for a,b in zip(weights,row)))-y
                for j in range(5):gradients[j]+=err*row[j]
            for j in range(5):weights[j]-=0.5*gradients[j]/len(data)
        self.weights=weights;self.fitted=True
    def classify(self,pixels):
        if not self.fitted:raise RuntimeError('model not fitted')
        x=features(pixels);score=sigmoid(sum(a*b for a,b in zip(self.weights,(1.,)+x)))
        return {'defect_probability':round(score,6),'decision':'REJECT' if score>=self.threshold else 'PASS',
                'features':dict(zip(('mean','edges','largest_cluster','dark_pixels'),x)),
                'review_required':abs(score-self.threshold)<.1}
    def to_json(self):return json.dumps({'threshold':self.threshold,'weights':self.weights,'fitted':self.fitted},sort_keys=True)
    @classmethod
    def from_json(cls,s):
        data=json.loads(s);obj=cls(data['threshold'])
        if len(data['weights'])!=5:raise ValueError('model shape mismatch')
        obj.weights=data['weights'];obj.fitted=data['fitted'];return obj

def read_pgm(source):
    """Supports plain P2 PGM fixtures; rejects unsupported formats and sizes."""
    tokens=[t for line in source.splitlines() if not line.lstrip().startswith('#') for t in line.split()]
    if len(tokens)<4 or tokens[0]!='P2':raise ImageError('only plain P2 PGM supported')
    try:
        w,h,maximum=map(int,tokens[1:4]);values=list(map(int,tokens[4:]))
    except ValueError as e:raise ImageError('invalid PGM header') from e
    if not (0<w*h<=4_000_000 and maximum==255 and len(values)==w*h):raise ImageError('invalid PGM size')
    pixels=[values[i*w:(i+1)*w] for i in range(h)];features(pixels);return pixels

if __name__=='__main__':
    print(features([[220]*8 for _ in range(8)]))
