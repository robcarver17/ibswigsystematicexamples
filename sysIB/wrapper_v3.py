from swigibpy import EWrapper
import time
import numpy as np
import datetime
from swigibpy import EPosixClientSocket

MEANINGLESS_ID=502

def return_IB_connection_info():
    """
    Returns the tuple host, port, clientID required by eConnect
   
    """
   
    host=""
   
    port=4001
    clientid=999
   
    return (host, port, clientid)

class IBWrapper(EWrapper):
    """

    Callback object passed to TWS, these functions will be called directly by the TWS or Gateway.

    """

    def error(self, id, errorCode, errorString):
        """
        error handling, simple for now
       
        Here are some typical IB errors
        INFO: 2107, 2106
        WARNING 326 - can't connect as already connected
        CRITICAL: 502, 504 can't connect to TWS.
            200 no security definition found
            162 no trades

        """
        global iserror
        global finished

        ## Any errors not on this list we just treat as information
        ERRORS_TO_TRIGGER=[201, 103, 502, 504, 509, 200, 162, 420, 2105, 1100, 478, 201, 399]
       
        if errorCode in ERRORS_TO_TRIGGER:
            iserror=True
            errormsg="IB error id %d errorcode %d string %s" %(id, errorCode, errorString)
            print errormsg
            finished=True  
           
        ## Wrapper functions don't have to return anything this is to tidy
        return 0
       
    def nextValidId(self, orderId):
        pass
   
    def managedAccounts(self, openOrderEnd):
        pass

    
    def realtimeBar(self, reqId, time, open, high, low, close, volume, wap, count):

        """
        Note we don't use all the information here
        
        Just append close prices. 
        """
    
        global pricevalue
        global finished

        pricevalue.append(close)


    def tickString(self, TickerId, field, value):
        global marketdata

        ## update string ticks

        tickType=field

        if int(tickType)==0:
            ## bid size
            marketdata[0]=int(value)
        elif int(tickType)==3:
            ## ask size
            marketdata[1]=int(value)

        elif int(tickType)==1:
            ## bid
            marketdata[0][2]=float(value)
        elif int(tickType)==2:
            ## ask
            marketdata[0][3]=float(value)
        


    def tickGeneric(self, TickerId, tickType, value):
        global marketdata

        ## update generic ticks

        if int(tickType)==0:
            ## bid size
            marketdata[0]=int(value)
        elif int(tickType)==3:
            ## ask size
            marketdata[1]=int(value)

        elif int(tickType)==1:
            ## bid
            marketdata[2]=float(value)
        elif int(tickType)==2:
            ## ask
            marketdata[3]=float(value)
        
        
        
           
    def tickSize(self, TickerId, tickType, size):
        
        ## update ticks of the form new size
        
        global marketdata

        
        if int(tickType)==0:
            ## bid
            marketdata[0]=int(size)
        elif int(tickType)==3:
            ## ask
            marketdata[1]=int(size)
        

   
    def tickPrice(self, TickerId, tickType, price, canAutoExecute):
        ## update ticks of the form new price
        
        global marketdata
        
        if int(tickType)==1:
            ## bid
            marketdata[2]=float(price)
        elif int(tickType)==2:
            ## ask
            marketdata[3]=float(price)
        
    
    def updateMktDepth(self, id, position, operation, side, price, size):
        """
        Only here for completeness - not required. Market depth is only available if you subscribe to L2 data.
        Since I don't I haven't managed to test this.
        
        Here is the client side call for interest
        
        tws.reqMktDepth(999, ibcontract, 9)
        
        """
        pass

        
    def tickSnapshotEnd(self, tickerId):
        finished=True





class IBclient(object):
    """
    Client object
    
    Used to interface with TWS for outside world, does all handling of streaming waiting etc
    
    Create like this
    callback = IBWrapper()
    client=IBclient(callback)

    We then use various methods to get prices etc

    """
    def __init__(self, callback):
        """
        Create like this
        callback = IBWrapper()
        client=IBclient(callback)
        """
        
        tws = EPosixClientSocket(callback)
        (host, port, clientid)=return_IB_connection_info()
        tws.eConnect(host, port, clientid)

        self.tws=tws


        
    def get_IB_market_data(self, ibcontract, seconds=30):
        """
        Returns more granular market data
        
        Returns a tuple (bid price, bid size, ask price, ask size)
        
        """
        
        global marketdata
        global finished
        global iserror
    
    
        finished=False
        iserror=False
        
        ## initialise the tuple
        marketdata=[np.nan, np.nan, np.nan, np.nan]
            
        # Request a market data stream 
        self.tws.reqMktData(
                MEANINGLESS_ID,
                ibcontract,
                "",
                False)       
        
        start_time=time.time()
        while not finished:
            if (time.time() - start_time) > seconds:
                finished=True
            pass
        self.tws.cancelMktData(MEANINGLESS_ID)
        
        ## marketdata should now contain some interesting information
        ## Note in this implementation we overwrite the contents with each tick; we could keep them
        
        if iserror:
            raise Exception("Problem getting market data")
        
        return marketdata
    
    
    
    def get_IB_snapshot_prices(self, ibcontract):
        
        """
        Returns a list of snapshotted prices, averaged over 'real time bars'
        
        tws is a result of calling IBConnector()
        
        """
        
        tws=self.tws
        
        global finished
        global iserror
        global pricevalue
    
    
        iserror=False
        
        finished=False
        pricevalue=[]
            
        # Request current price in 5 second increments
        # It turns out this is the only way to do it (can't get any other increments)
        tws.reqRealTimeBars(
                MEANINGLESS_ID,                                          # tickerId,
                ibcontract,                                   # contract,
                5, 
                "MIDPOINT",
                0)
    
    
        start_time=time.time()
        ## get about 16 seconds worth of samples
        ## could obviously just stop at N bars as well eg. while len(pricevalue)<N:
        
        while not finished:
            if iserror:
                finished=True
            if (time.time() - start_time) > 20: ## get ~4 samples over 15 seconds
                finished=True
            pass
        
        ## Cancel the stream
        tws.cancelRealTimeBars(MEANINGLESS_ID)

        if len(pricevalue)==0 or iserror:
            raise Exception("Failed to get price")

        
        return pricevalue
