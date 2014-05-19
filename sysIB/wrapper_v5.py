from swigibpy import EWrapper
import time
from swigibpy import EPosixClientSocket, ExecutionFilter

from swigibpy import Order as IBOrder
from sysIB.IButils import bs_resolve, action_ib_fill

MAX_WAIT_SECONDS=10
MEANINGLESS_NUMBER=1830

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
       
    """
    Following methods will be called, but we don't use them
    """

    def nextValidId(self, id):
        pass
       
    def managedAccounts(self, openOrderEnd):
        pass

    def orderStatus(self, reqid, status, filled, remaining, avgFillPrice, permId,
            parentId, lastFilledPrice, clientId, whyHeld):
        pass

    def commissionReport(self, blah):
        pass


    def contractDetailsEnd(self, reqId):
        """
        Finished getting contract details
        """
        
        global finished
        finished=True

    def contractDetails(self, reqId, contractDetails):
        """
        Return contract details
        
        If you submit more than one request watch out to match up with reqId
        """
        
        global contract_details

        contract_details={}
        contract_details["contractMonth"]=contractDetails.contractMonth
        contract_details["liquidHours"]=contractDetails.liquidHours
        contract_details["longName"]=contractDetails.longName
        contract_details["minTick"]=contractDetails.minTick
        contract_details["tradingHours"]=contractDetails.tradingHours
        contract_details["timeZoneId"]=contractDetails.timeZoneId
        contract_details["underConId"]=contractDetails.underConId
        contract_details["evRule"]=contractDetails.evRule
        contract_details["evMultiplier"]=contractDetails.evMultiplier

        contract2 = contractDetails.summary

        contract_details["expiry"]=contract2.expiry

        contract_details["exchange"]=contract2.exchange
        contract_details["symbol"]=contract2.symbol
        contract_details["secType"]=contract2.secType
        contract_details["currency"]=contract2.currency

    def updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName):
        """
        Add a row to the portfolio structure
        """

                
        portfolio_structure.append((contract.symbol, contract.expiry, position, marketPrice, marketValue, averageCost, 
                                    unrealizedPNL, realizedPNL, accountName, contract.currency))

    def updateAccountValue(self, key, value, currency, accountName):
        """
        Populates account value dictionary
        """
        account_value.append((key, value, currency, accountName))
        

    def accountDownloadEnd(self, accountName):
        """
        Finished can look at portfolio_structure and account_value
        """

        finished=True

    def updateAccountTime(self, timeStamp):
        pass 




class IBclient(object):
    """
    Client object
    
    Used to interface with TWS for outside world, does all handling of streaming waiting etc
    
    Create like this
    callback = IBWrapper()
    client=IBclient(callback)

    We then use various methods to get prices etc

    """
    def __init__(self, callback, accountid="DU15237"):
        """
        Create like this
        callback = IBWrapper()
        client=IBclient(callback)
        """
        
        tws = EPosixClientSocket(callback)
        (host, port, clientid)=return_IB_connection_info()
        tws.eConnect(host, port, clientid)

        self.tws=tws
        self.accountid=accountid


    
    def get_contract_details(self, ibcontract):
    
        """
        Returns a dictionary of contract_details
        
        
        """
        
        global finished
        global iserror
        global contract_details
    
        finished=False
        iserror=False
        contract_details={}
        
        self.tws.reqContractDetails(
            MEANINGLESS_NUMBER,                                         # reqId,
            ibcontract,                                   # contract,
        )
    
        
        start_time=time.time()
        while not finished:
            if (time.time() - start_time) > MAX_WAIT_SECONDS:
                finished=True
                iserror=True
            pass
    
        if iserror or contract_details=={}:
            raise Exception("Problem getting details")
    
        return contract_details

    def get_IB_account_data(self):
        global finished
        global iserror
        global account_value

        finished=False
        iserror=False
        account_value=[]

        ## Turn on the streaming of accounting information
        self.tws.reqAccountUpdates(True, self.accountid)
        start_time=time.time()
        while not finished:
            if (time.time() - start_time) > MAX_WAIT_SECONDS:
                finished=True
                iserror=True
            pass

        ## Turn off the streaming
        ## Note portfolio_structure will also be updated
        self.tws.reqAccountUpdates(False, self.accountid)

        if len(account_value)==0 or iserror:
            msg="No account data recieved"
            raise Exception(msg)

        return account_value

    def get_IB_positions(self):

        """
        Returns positions held - a particular kind of accounting information
        """


        global finished
        global iserror
        global portfolio_structure
        global account_value

        finished=False
        iserror=False
        portfolio_structure=[]
        account_value=[]

        ## Ask to get accounting info, both positions and account details
        self.tws.reqAccountUpdates(True, self.accountid)
        start_time=time.time()
        while not finished:
            if (time.time() - start_time) > MAX_WAIT_SECONDS:
                finished=True
                iserror=True
            pass
        self.tws.reqAccountUpdates(False, self.accountid)

        exchange_rates={}

        ## Create a dictionary of exchange rates
        for x in account_value:
            if x[0]=="ExchangeRate":
                exchange_rates[x[2]]=float(x[1])

        return (portfolio_structure, exchange_rates)

        
