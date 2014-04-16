import pandas as pd
import numpy as np

DEFAULT_VALUE=np.nan

class autodf(object):
    '''
    Object to make it easy to add data in rows and return pandas time series
    
    Initialise with autodf("name1", "name2", ...)
    Add rows with autodf.add_row(name1=..., name2=...., )
    To data frame with autodf.to_pandas
    '''

    def __init__(self, *args):
        
        
        storage=dict()
        self.keynames=args
        for keyname in self.keynames:
            storage[keyname]=[]
            
        self.storage=storage 
        
    def add_row(self, **kwargs):
        
        for keyname in self.storage.keys():
            if keyname in kwargs:
                self.storage[keyname].append(kwargs[keyname])
            else:
                self.storage[keyname].append(DEFAULT_VALUE)

    def to_pandas(self, indexname=None):
        if indexname is not None:
            data=self.storage
            index=self.storage[indexname]
            data.pop(indexname)
            return pd.DataFrame(data, index=index)
        else:
            return pd.DataFrame(self.storage)
        
if __name__=="__main__":

    ans=autodf("datetime", "price", "volume")
    ans.add_row(datetime=pd.datetime(1985,12,1), price=25.9, volume=30)
    ans.add_row(datetime=pd.datetime(1985,12,2), price=25.9)
    ans.add_row(datetime=pd.datetime(1985,12,3), volume=40)
    print ans.to_pandas("datetime")
    