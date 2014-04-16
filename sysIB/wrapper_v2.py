from swigibpy import EWrapper
import time

import datetime
from swigibpy import EPosixClientSocket

from sysIB.IButils import autodf

### how many seconds before we give up
MAX_WAIT=30

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

        Callback object passed to TWS, these functions will be called directly
    by TWS.

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
       
    def currentTime(self, time_from_server):
        global the_time_now_is
        global finished
       
        the_time_now_is=time_from_server
        finished=True
       
    def nextValidId(self, orderId):
        pass
   
    def managedAccounts(self, openOrderEnd):
        pass


    def historicalData(self, reqId, date, openprice, high,
                       low, close, volume,
                       barCount, WAP, hasGaps):
        
        global historicdata
        global finished

        if date[:8] == 'finished':
            finished=True
        else:
            
            date=datetime.datetime.strptime(date,"%Y%m%d")
            historicdata.add_row(date=date, open=openprice, high=high, low=low, close=close, volume=volume)




class IBclient(object):
    def __init__(self, callback):
        tws = EPosixClientSocket(callback)
        (host, port, clientid)=return_IB_connection_info()
        tws.eConnect(host, port, clientid)

        self.tws=tws

    def speaking_clock(self):
        global the_time_now_is
        global finished
        global iserror
        
        print "Getting the time..."
        
        self.tws.reqCurrentTime()
        
        start_time=time.time()
        finished=False
        iserror=False
        
        the_time_now_is="didnt get time"
        
        while not finished:
            if (time.time() - start_time) > MAX_WAIT:
                finished=True
            pass
    
        if iserror:
            print "Error happened"
            
        return the_time_now_is


    
    
    
    
    
    def get_IB_historical_data(self, ibcontract, durationStr="1 Y", barSizeSetting="1 day", tickerid=999):
        
        """
        Returns historical prices for a contract, up to today
        
        tws is a result of calling IBConnector()
        
        """
        global historicdata
        global finished
        global iserror

        finished=False
        iserror=False
        today=datetime.datetime.now()
        
        historicdata=autodf("date", "open", "high", "low", "close", "volume")
            
        # Request some historical data.
        self.tws.reqHistoricalData(
                tickerid,                                          # tickerId,
                ibcontract,                                   # contract,
                today.strftime("%Y%m%d %H:%M:%S %Z"),       # endDateTime,
                durationStr,                                      # durationStr,
                barSizeSetting,                                    # barSizeSetting,
                "TRADES",                                   # whatToShow,
                1,                                          # useRTH,
                1                                           # formatDate
            )
        
        start_time=time.time()
        while not finished:
            if (time.time() - start_time) > MAX_WAIT:
                finished=True
                iserror=True
            pass
        
        if iserror:
            raise Exception("Problem getting historic data")
        
        results=historicdata.to_pandas("date")
        
        return results