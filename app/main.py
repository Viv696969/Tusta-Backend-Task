from trading import TradeLogger,TradingStrategy
import json

class User:
    def __init__(self,email=None):
        self.email=email #just for dummy purpose
        self.indicators={} #will be helpfull for scaling applications when we have higher number of indicators

    def getEmail(self):
        return self.email
    
    def setEmail(self,email):
        self.email=email

    def setIndicator(self,indicatorName,parameters):
        self.indicators[indicatorName]=parameters

    def listIndicators(self):
        indicatorList=[]
        for name in self.indicators:
            indicatorList.append(name)
        return indicatorList
    
    def getIndicatorDetails(self,name):
        return self.indicators.get(name,None)
    

def main():
    inputData=json.load(open("config.json"))
    # enter user details and create object
    user=User(inputData["email"])
    
    print("Your available Indicators are ->",user.listIndicators())
    # below inputs can be taken by frontend also during development ; can put validation condition that value should be between 10 to 90
    while True:
        period=inputData["period"]
        if 0<period<20:break
        print("Invalid RSI period entered..Try Again")
    
    buyThreshold=inputData["buyThreshold"]
    sellThreshold=inputData["sellThreshold"]
    user.setIndicator("rsi",{"period":period,"buyThreshold":buyThreshold,"sellThreshold":sellThreshold})
    print("RSI indicator details -> ",user.getIndicatorDetails("rsi"))

    trading=TradingStrategy()
    for index,value in enumerate(trading.getCompanies()):
        print(f"{index} {value}")
    companyIndex=inputData["companyIndex"]
    # based on the user choice from the frontend we can invoke respective method
    logs=trading.tradeRSI(user.getIndicatorDetails("rsi"),companyIndex) #other fields can be taken too
    tradeLogger=TradeLogger()
    tradeLogger.logRsiLogs(logs,user.email,trading.getCompanies()[companyIndex].split(" -> ")[0])

if __name__=="__main__":
    main()


    
    