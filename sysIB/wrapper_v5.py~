from swigibpy import EWrapper
import time
from swigibpy import EPosixClientSocket, ExecutionFilter

from swigibpy import Order as IBOrder
from sysIB.IButils import bs_resolve, action_ib_fill

MAX_WAIT_SECONDS=10
MEANINGLESS_NUMBER=1729

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
       
    def managedAccounts(self, openOrderEnd):
        pass

    def orderStatus(self, reqid, status, filled, remaining, avgFillPrice, permId,
            parentId, lastFilledPrice, clientId, whyHeld):
        pass

    def commissionReport(self, blah):
        pass


    def execDetails(self, reqId, contract, execution):
    
        """
        This is called if 
        
        a) we have submitted an order and a fill has come back (in which case getting_executions is False)
        b) We have asked for recent fills to be given to us (in which case it is True)
        
        In case (a) we call action_ib_fill with the fill details; and for case (b) we add the fill to a list 
        
        See API docs, C++, SocketClient Properties, Contract and Execution for more details 
        """
        
        global execlist
        global getting_executions    
            
        
        execid=execution.execId
        exectime=execution.time
        thisorderid=execution.orderId
        account=execution.acctNumber
        exchange=execution.exchange
        permid=execution.permId
        avgprice=execution.price
        cumQty=execution.cumQty
        clientid=execution.clientId
        symbol=contract.symbol
        expiry=contract.expiry
        side=execution.side
        
        execdetails=dict(side=str(side), times=str(exectime), orderid=str(thisorderid), qty=int(cumQty), price=float(avgprice), symbol=str(symbol), expiry=str(expiry), clientid=str(clientid), execid=str(execid), account=str(account), exchange=str(exchange), permid=int(permid))

        if getting_executions:        
            execlist.append(execdetails)
        else:
            ## one off fill
            action_ib_fill(execdetails)
            
    def execDetailsEnd(self, reqId):
        """
        No more orders to look at if execution details requested
        """
        
        global finished
        finished=True
            
        

    def openOrder(self, orderID, contract, order, orderState):
        """
        Tells us about any orders we are working now
        
        Note these objects are not persistent or interesting so we have to extract what we want
        
        
        """
        
        global order_structure

        ## Get a selection of interesting things about the order
        orderdict=dict(symbol=contract.symbol , expiry=contract.expiry,  qty=int(order.totalQuantity) , 
                       side=order.action , orderid=orderID, clientid=order.clientId ) 
        
        order_structure.append(orderdict)

    def nextValidId(self, orderId):
        """
        Give the next valid order id 
        
        Note this doesn't 'burn' the ID; if you call again without executing the next ID will be the same
        """
        
        global brokerorderid
        global finished
        brokerorderid=orderId

    def openOrderEnd(self):
        """
        Finished getting open orders
        """
        global finished
        finished=True

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



    def get_next_brokerorderid(self):
        """
        Get the next brokerorderid
        """

        global finished
        global brokerorderid
        global iserror
        
        finished=False
        brokerorderid=None
        iserror=False

        start_time=time.time()
        
        ## Note for more than one ID change '1'
        self.tws.reqIds(1)
        while not finished:
            if (time.time() - start_time) > MAX_WAIT_SECONDS:
                finished=True
            if brokerorderid is not None:
                finished=True
                
            pass
        
        if brokerorderid is None or iserror:
            
            raise Exception("Problem getting next broker orderid")
        
        return brokerorderid


    def place_new_IB_order(self, ibcontract, trade, lmtPrice, orderType, orderid=None):
        """
        Places an order
        
        Returns brokerorderid
    
        raises exception if fails
        """
        global iserror
        global brokerorderid
        global finished
        global getting_executions
        global order_structure
        
        iborder = IBOrder()
        iborder.action = bs_resolve(trade)
        iborder.lmtPrice = lmtPrice
        iborder.orderType = orderType
        iborder.totalQuantity = abs(trade)
        iborder.tif='DAY'
        iborder.transmit=True

        
        getting_executions=False
        order_structure=[]

        ## We can eithier supply our own ID or ask IB to give us the next valid one
        if orderid is None:
            print "Getting orderid from IB"
            orderid=self.get_next_brokerorderid()
            
        
        print "Using order id of %d" % orderid
    
         # Place the order
        self.tws.placeOrder(
                orderid,                                    # orderId,
                ibcontract,                                   # contract,
                iborder                                       # order
            )
    
        return orderid

    def any_open_orders(self):
        """
        Simple wrapper to tell us if we have any open orders
        """
        
        return len(self.get_open_orders())>0

    def get_open_orders(self):
        """
        Returns a list of any open orders
        """
        
        
        global finished
        global iserror
        global order_structure
        
        iserror=False
        finished=False
        order_structure=[]
        
        start_time=time.time()
        self.tws.reqAllOpenOrders()
        
        while not finished:
            if (time.time() - start_time) > MAX_WAIT_SECONDS:
                ## You should have thought that IB would teldl you we had finished
                finished=True
            pass
        
        if iserror:
            raise Exception("Problem getting open orders")
    
        return order_structure    
    


    def get_executions(self):
        """
        Returns a list of all executions done today
        """
        
        
        global finished
        global iserror
        global execlist
        global getting_executions
        
        iserror=False
        finished=False
        execlist=[]
        
        ## Tells the wrapper we are getting executions, not expecting fills
        ## Note that if you try and get executions when fills should be coming will be confusing!
        ## BE very careful with fills code
        
        getting_executions=True
        
        start_time=time.time()
        
        ## We can change ExecutionFilter to subset different orders
        
        self.tws.reqExecutions(MEANINGLESS_NUMBER, ExecutionFilter())
        
        while not finished:
            if (time.time() - start_time) > MAX_WAIT_SECONDS:
                finished=True
                iserror=True
            pass
    
        ## Change this flag back so that the process gets fills properly
        getting_executions=False
        
        if iserror:
            raise Exception("Problem getting executions")
        
        return execlist
        
