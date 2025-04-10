import KIS_Common as Common

import pandas as pd
import pprint

Common.SetChangeMode("VIRTUAL") 


#####################################################
TestArea = "US" #한국이라면 KR 미국이라면 US로 변경하세요 ^^
#####################################################

#테스트할 종목 넣기!!
stock_code = "TLT" # 미국 : QQQ, TLT 기타 등등 한국: 133690,005930

GetCount = 700  #얼마큼의 데이터를 가져올 것인지 
CutCount = 0     #최근 데이터 삭제! 200으로 세팅하면 200개의 최근 데이터가 사라진다

fee = 0.0025 #수수료+세금+슬리피지를 매수매도마다 0.15%로 기본 세팅!

TotalMoney = 1000000 #한국 계좌의 경우 시작 투자금 100만원으로 가정!

if TestArea == "US": #미국의 경우는
    TotalMoney = 1000 #시작 투자금 $1000로 가정!
    




RealTotalList = list() #최종 결과가 저장될 리스트


print("\n----stock_code: ", stock_code)

#일봉 캔들 정보를 가지고 온다!
df = Common.GetOhlcv(TestArea,stock_code, GetCount) 

'''
############# 이동평균선! ###############
for ma in range(3,201): #3일선 부터 200일선을 구한다.
    df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()
########################################
#아래 최적화된 코드로 변경되었어요!
'''

############# 이동평균선! ###############
ma_dfs = []

# 이동 평균 계산
for ma in range(3, 201):
    ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
    ma_dfs.append(ma_df)

# 이동 평균 데이터 프레임을 하나로 결합
ma_df_combined = pd.concat(ma_dfs, axis=1)

# 원본 데이터 프레임과 결합
df = pd.concat([df, ma_df_combined], axis=1)
########################################


df.dropna(inplace=True) #데이터 없는건 날린다!

df = df[:len(df)-CutCount] #최신 데이터 몇 개를 날리는 부분 CutCount값이 0이라면 최근 데이터까지!
pprint.pprint(df)


print("테스트하는 총 금액: ", round(TotalMoney))


print("이평선 조합 체크 중....")
for ma1 in range(3,21): #3일선 부터 20일선까지
    for ma2 in range(20,201): #20일선 부터 200일선 까지
                
        IsBuy = False #매수 했는지 여부
        BUY_PRICE = 0  #매수한 금액! 

        TryCnt = 0      #매매횟수
        SuccesCnt = 0   #익절 숫자
        FailCnt = 0     #손절 숫자

        InvestMoney = TotalMoney #초기 투자금 설정
        TotalMoneyList = list() #투자금 이력 리스트

        #'''
        #####################################################
        ##########골든 크로스에서 매수~ 데드크로스에서 매도~!##########
        #####################################################
        for i in range(len(df)):


            NowClosePrice = df['close'].iloc[i]    #오늘 종가
            PrevClosePrice = df['close'].iloc[i-1] #전일 종가
            
            
            #매수 상태!
            if IsBuy == True:

                #투자금의 등락률을 매일 매일 반영!
                InvestMoney = InvestMoney * (1.0 + ((NowClosePrice - PrevClosePrice) / PrevClosePrice))
                            
                #단기 이동평균선이 장기 이동평균선 보다 작은데 단기 이동평균선이 감소중이라면 매도 처리!
                if df[str(ma1)+'ma'].iloc[i-1] < df[str(ma2)+'ma'].iloc[i-1] and df[str(ma1)+'ma'].iloc[i-2] > df[str(ma1)+'ma'].iloc[i-1]:  #데드 크로스!


                    #진입(매수)가격 대비 변동률
                    Rate = (NowClosePrice - BUY_PRICE) / BUY_PRICE

                    RevenueRate = (Rate - fee)*100.0 #수익률 계산

                    InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                    #print(stock_code ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매도!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(InvestMoney,2)  , " ", df['open'].iloc[i])
                    #print("\n\n")

                    TryCnt += 1 #매매 횟수

                    if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                        SuccesCnt += 1 #성공
                    else:
                        FailCnt += 1 #실패


                    IsBuy = False #매도했다

            #아직 매수전 상태
            if IsBuy == False:

                #단기 이동평균선이 장기 이동평균선보다 크고 단기 이동평균선이 증가중일 경우! 매수한다!!
                if i >= 2 and df[str(ma1)+'ma'].iloc[i-1] > df[str(ma2)+'ma'].iloc[i-1] and df[str(ma1)+'ma'].iloc[i-2] < df[str(ma1)+'ma'].iloc[i-1]:  #골든 크로스!

                    BUY_PRICE = NowClosePrice  #매수가격은 종가로 가정!

                    InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                    #print(stock_code ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매수! ,종목 잔고:", round(InvestMoney,2) , " ", df['open'].iloc[i])
                    IsBuy = True #매수했다

            
            TotalMoneyList.append(InvestMoney)  #투자금 변경이력을 리스트에 저장!

        #####################################################
        #####################################################
        #####################################################
        #'''
        


        #결과 정리 및 데이터 만들기!!
        if len(TotalMoneyList) > 0:

            resultData = dict()

            
            resultData['Ticker'] = stock_code

            #이동평균 매매 전략 성과 구하기
            result_df = pd.DataFrame({ "Total_Money" : TotalMoneyList}, index = df.index)

            result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
            result_df['Cum_Ror'] = result_df['Ror'].cumprod()

            result_df['Highwatermark'] =  result_df['Cum_Ror'].cummax()
            result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
            result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

            resultData['DateStr'] = str(result_df.iloc[0].name) + " ~ " + str(result_df.iloc[-1].name)

            resultData['OriMoney'] = TotalMoney
            resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
            resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)
            resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0

            resultData['TryCnt'] = TryCnt
            resultData['SuccesCnt'] = SuccesCnt
            resultData['FailCnt'] = FailCnt

            

            #'''
            #각 결과 로그 뿌려주기..
            print("############ ",resultData['DateStr']," ##########")
                                        
            print("-- ma1", ma1, " -- ma2 : ", ma2)
            print("---------- 총 결과 ----------")
            print("최초 금액:", str(format(round(resultData['OriMoney']), ','))  , " 최종 금액:", str(format(round(resultData['FinalMoney']), ',')), "\n수익률:", format(round(((resultData['FinalMoney'] - resultData['OriMoney']) / resultData['OriMoney']) * 100,2),',') ,"% MDD:",  round(resultData['MDD'],2),"%")
            print("------------------------------")
            print("####################################")
            #'''


            #조합 결과 데이터 만들기!
            FinalResultData = dict()
            FinalResultData['day_str'] = resultData['DateStr']
            FinalResultData['stock_ticker'] = stock_code
            FinalResultData['ma_str'] = str(ma1) + " " + str(ma2) 
            FinalResultData['RevenueRate'] = round(((resultData['FinalMoney'] - resultData['OriMoney']) / resultData['OriMoney']) * 100,2)
            FinalResultData['MDD'] = round(resultData['MDD'],2)


            RealTotalList.append(FinalResultData)
            
            TotalMoneyList.clear()
            
    

print(stock_code, " 체크 끝!!!!!!!")
print("#####################################################################")



df_all = pd.DataFrame(RealTotalList)

#엑셀로 데이터를 내보내기 (결과 엑셀 파일 생성!)
df_all.to_excel("./"+stock_code + '_ma_test_all_data.xlsx', index=False)


#결과 보여주기 프린트문!!
print("#####################################################################")
print("#####################################################################\n")
Ticker = df_all['stock_ticker'].iloc[-1]
print("대상 종목 : ", Ticker)
print("테스트 기간: ", df_all['day_str'].iloc[-1],"\n")

df_all = df_all.drop('day_str', axis=1)
df_all = df_all.drop('stock_ticker', axis=1)

df_all['RevenueRate_rank'] = df_all['RevenueRate'].rank(ascending=True)
df_all['MDD_rank'] = df_all['MDD'].rank(ascending=True)
df_all['Score'] = df_all['RevenueRate_rank'] + df_all['MDD_rank']

df_all = df_all.sort_values(by="RevenueRate_rank",ascending=False)
print(">>>>>>>>>> ",Ticker," 수익률 TOP10 >>>>>>>>>>>>>>>>")
pprint.pprint(df_all.head(10))

df_all = df_all.sort_values(by="MDD_rank",ascending=False)
print("\n>>>>>>>>>> ",Ticker," MDD TOP10 >>>>>>>>>>>>>>>>")
pprint.pprint(df_all.head(10))

df_all = df_all.sort_values(by="Score",ascending=False)
print("\n>>>>>>>>>> ",Ticker," (수익률랭크+MDD랭크)랭킹 TOP10 >>>>>>>>>>>>>>>>")
pprint.pprint(df_all.head(10))

print("#####################################################################")
print("#####################################################################\n\n")


print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")









