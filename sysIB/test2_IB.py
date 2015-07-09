from sysIB.wrapper_v2 import IBWrapper, IBclient
from swigibpy import Contract as IBcontract
from matplotlib.pyplot import show
 
if __name__=="__main__":

    """
    This simple example returns the time 
    """

    callback = IBWrapper()
    client=IBclient(callback)
    
    ibcontract = IBcontract()
    ibcontract.secType = "FUT"
    ibcontract.expiry="201809"
    ibcontract.symbol="GE"
    ibcontract.exchange="GLOBEX"

    ans=client.get_IB_historical_data(ibcontract)
    ans.close.plot()
    show()
     
