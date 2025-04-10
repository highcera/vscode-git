import KIS_Common as Common

import pandas as pd
import pprint
import matplotlib.pyplot as plt


Common.SetChangeMode("VIRTUAL") 

#####################################################
TestArea = "US" #한국이라면 KR 미국이라면 US로 변경하세요 ^^
#####################################################

#테스트할 종목 넣기!!
stock_code = "TLT" #미국 : QQQ, TLT 기타 등등 한국: 133690,005930

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
############# 테스팅할 이동평균 설정!! ###############
small_ma = 18
big_ma = 55
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$




fee = 0.0025 #수수료+세금+슬리피지를 매수매도마다 0.25%로 기본 세팅!

TotalMoney = 1000000 #한국 계좌의 경우 시작 투자금 100만원으로 가정!

if TestArea == "US": #미국의 경우는
    TotalMoney = 1000 #시작 투자금 $1000로 가정!

GetCount = 700 #얼마큼의 데이터를 가져올 것인지
CutCount = 0     #최근 데이터 삭제! 200으로 세팅하면 200개의 최근 데이터가 사라진다



InvestMoney = TotalMoney     #초기 투자금 세팅 (이동평균 매매 전략용)
OriInvestMoney = TotalMoney  #초기 투자금 세팅 (단순보유용)


#일봉 캔들 정보를 가지고 온다!
df = Common.GetOhlcv(TestArea, stock_code, GetCount) 

############# 이동평균선! ###############
df['small_ma'] = df['close'].rolling(small_ma).mean() #단기 이동평균선을 구한다!
df['big_ma'] = df['close'].rolling(big_ma).mean() #장기 이동평균선을 구한다!

df['max_ma'] = df['close'].rolling(200).mean() #200일선을 구하는 이유는 테스팅 기간을 동일하게 하기 위해!
########################################

df.dropna(inplace=True) #이 코드로 데이터 없는것을 날리는데 동일하게 199개의 데이터를 날리기 위해 (200일 이동평균선 데이터가 없는 1~199일의 구간)

df = df[:len(df)-CutCount] #최신 데이터 몇 개를 날리는 부분 CutCount값이 0이라면 최근 데이터까지!

pprint.pprint(df) #일봉 캔들 정보를 프린트 해본다.


IsBuy = False #매수 했는지 여부
BUY_PRICE = 0  #매수한 금액! 

TryCnt = 0      #매매횟수
SuccesCnt = 0   #익절 숫자
FailCnt = 0     #손절 숫자


TotalMoneyList = list()     #투자금 이력 리스트 (이동평균 매매 전략용)
OriTotalMoneyList = list()  #투자금 이력 리스트 (단순보유용)

#'''
#####################################################
##########골든 크로스에서 매수~ 데드크로스에서 매도~!##########
#####################################################
for i in range(len(df)):


    NowClosePrice = df['close'].iloc[i]     #오늘 종가
    PrevClosePrice = df['close'].iloc[i-1]  #전일 종가
    
    if i >= 1:
        OriInvestMoney = OriInvestMoney * (1.0 + ((NowClosePrice - PrevClosePrice) / PrevClosePrice)) #단순 보유의 등락률을 투자금에 반영한다.
    
    #매수 된 상태!
    if IsBuy == True:

        InvestMoney = InvestMoney * (1.0 + ((NowClosePrice - PrevClosePrice) / PrevClosePrice)) #이동평균 매매 전략의 등락률을 투자금에 반영한다.
                    
        
        #단기 이동평균선이 장기 이동평균선 보다 작은데 단기 이동평균선이 감소중일 경우!!! 매도처리 한다!
        if df['small_ma'].iloc[i-1] < df['big_ma'].iloc[i-1] and df['small_ma'].iloc[i-2] > df['small_ma'].iloc[i-1] :

            #진입(매수)가격 대비 변동률
            Rate = (NowClosePrice - BUY_PRICE) / BUY_PRICE

            RevenueRate = (Rate - fee)*100.0 #수익률 계산

            InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

            print(stock_code ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매도!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(InvestMoney,2)  , " ", df['open'].iloc[i])
            print("\n\n")


            TryCnt += 1 #매매 횟수

            if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                SuccesCnt += 1 #성공
            else:
                FailCnt += 1 #실패


            IsBuy = False #매도했다

    #아직 매수 전 상태!
    if IsBuy == False:

        #단기 이동평균선이 장기 이동평균선보다 크고 단기 이동평균선이 증가중일 경우! 매수한다!!
        if i >= 2 and df['small_ma'].iloc[i-1] > df['big_ma'].iloc[i-1] and df['small_ma'].iloc[i-2] < df['small_ma'].iloc[i-1]:
            
            BUY_PRICE = NowClosePrice  #매수가격은 종가로 가정!

            InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

            print(stock_code ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매수! ,종목 잔고:", round(InvestMoney,2) , " ", df['open'].iloc[i])
            IsBuy = True #매수했다

    
    TotalMoneyList.append(InvestMoney)        #투자금 변경이력을 리스트에 저장! (이동평균 매매 전략용)
    OriTotalMoneyList.append(OriInvestMoney)  #투자금 변경이력을 리스트에 저장! (단순보유용)

#####################################################
#####################################################
#####################################################
#'''


#결과 정리 및 데이터 만들기!!
if len(TotalMoneyList) > 0:

    resultData = dict()

    
    resultData['Ticker'] = stock_code




    #단순 보유 성과 구하기
    ori_result_df = pd.DataFrame({ "OriTotal_Money" : OriTotalMoneyList}, index = df.index)
    
    # CAGR 계산을 위한 연수 계산
    start_date = pd.to_datetime(df.index[0])
    end_date = pd.to_datetime(df.index[-1])
    years = (end_date - start_date).days / 365.25
    
    # 단순 보유 CAGR 계산
    ori_total_return = (ori_result_df['OriTotal_Money'].iloc[-1] / ori_result_df['OriTotal_Money'].iloc[0])
    ori_cagr = (ori_total_return ** (1/years) - 1) * 100

    # 전략 CAGR 계산
    strategy_total_return = (TotalMoneyList[-1] / TotalMoneyList[0])
    strategy_cagr = (strategy_total_return ** (1/years) - 1) * 100
    
    # 결과 데이터에 CAGR 추가
    resultData['Ori_CAGR'] = ori_cagr
    resultData['Strategy_CAGR'] = strategy_cagr

    ori_result_df['OriRor'] = ori_result_df['OriTotal_Money'].pct_change() + 1
    ori_result_df['OriCum_Ror'] = ori_result_df['OriRor'].cumprod()

    ori_result_df['OriHighwatermark'] =  ori_result_df['OriCum_Ror'].cummax()
    ori_result_df['OriDrawdown'] = (ori_result_df['OriCum_Ror'] / ori_result_df['OriHighwatermark']) - 1
    ori_result_df['OriMaxDrawdown'] = ori_result_df['OriDrawdown'].cummin()
    
    
    #이동평균 매매 전략 성과 구하기
    result_df = pd.DataFrame({ "Total_Money" : TotalMoneyList}, index = df.index)

    result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
    result_df['Cum_Ror'] = result_df['Ror'].cumprod()

    result_df['Highwatermark'] =  result_df['Cum_Ror'].cummax()
    result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
    result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()


    #결과 데이터 만들기!
    resultData['DateStr'] = str(result_df.iloc[0].name) + " ~ " + str(result_df.iloc[-1].name)

    resultData['StartMoney'] = TotalMoney
    resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
    resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)
    resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0

    resultData['Ori_StartMoney'] = ori_result_df['OriTotal_Money'].iloc[0]
    resultData['Ori_FinalMoney'] = ori_result_df['OriTotal_Money'].iloc[-1]
    resultData['Ori_RevenueRate'] = ((ori_result_df['OriCum_Ror'].iloc[-1] -1.0)* 100.0)
    resultData['Ori_MDD'] = ori_result_df['OriMaxDrawdown'].min() * 100.0
    
    resultData['TryCnt'] = TryCnt
    resultData['SuccesCnt'] = SuccesCnt
    resultData['FailCnt'] = FailCnt
    


    #여기서 부터 차트를 그려주기 위한 코드!!!!
    result_df.index = pd.to_datetime(result_df.index)
    ori_result_df.index = pd.to_datetime(ori_result_df.index)

    fig, axs = plt.subplots(2, 1, figsize=(10, 10))

    axs[0].plot(result_df['Cum_Ror'] * 100, label='Strategy')
    axs[0].plot(ori_result_df['OriCum_Ror'] * 100, label='Buy & Hold', linestyle='--', alpha = 0.3)
    axs[0].set_ylabel('Cumulative Return (%)')
    axs[0].set_title(stock_code + ' Chart')
    axs[0].legend()

    #전략의 MDD 보여주기!
    axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='Strategy MDD')
    axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Strategy Drawdown')
    
    #단순보유 MDD 보여주기!
    axs[1].plot(result_df.index, ori_result_df['OriMaxDrawdown'] * 100, label='Buy & Hold MDD', linestyle='--', alpha = 0.3)
    axs[1].plot(result_df.index, ori_result_df['OriDrawdown'] * 100, label='Buy & Hold Drawdown', linestyle='--', alpha = 0.3)
    
    axs[1].set_ylabel('Drawdown (%)')
    axs[1].set_title(stock_code + ' Drawdown Chart')
    axs[1].legend()

    # Show the plot
    plt.tight_layout()
    plt.show()
    
    
    
    
    
    
    #최종 결과를 뿌려주는 프린트 문!!!
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
    print("\n종목 코드: ", resultData['Ticker'] )
    print("테스트 기간: ",resultData['DateStr'].replace("00:00:00",""))
    print("\n---------------단순 보유---------------")
    print("최초 금액: ", format(int(round(resultData['Ori_StartMoney'],0)), ',') , " 최종 금액: ",  format(int(round(resultData['Ori_FinalMoney'],0)), ',') )
    print("수익률:", format(round(resultData['Ori_RevenueRate'],2), ',') , "%  MDD:", round(resultData['Ori_MDD'],2) , "%")
    print("연복리 수익률 CAGR: ", format(round(resultData['Ori_CAGR'],2), ','), "%")
    print("-----------------------------------------------")
    print("\n---------------전략 성과---------------")
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")
    print(">>",small_ma, "일 이평선 &", big_ma, "일 이평선","<<\n")
    print("최초 금액: ", format(int(round(resultData['StartMoney'],0)), ',') , " 최종 금액: ",  format(int(round(resultData['FinalMoney'],0)), ',') )
    print("수익률:", format(round(resultData['RevenueRate'],2), ',') , "%  MDD:", round(resultData['MDD'],2) , "%")
    print("연복리 수익률 CAGR: ", format(round(resultData['Strategy_CAGR'],2), ','), "%")
    if resultData['TryCnt'] > 0:
        print("(성공:", resultData['SuccesCnt'] , " 실패:", resultData['FailCnt']," -> 승률: ", round(resultData['SuccesCnt']/resultData['TryCnt'] * 100.0,2) ,"%)\n")
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print("-----------------------------------------------\n")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")