import pandas as pd
import logging
from strategy import TradingStrategy
from data_fetcher import DataFetcher
from config import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, initial_balance=10000.0, trade_amount=100.0, fee_rate=0.001):
        """
        백테스터 초기화
        :param initial_balance: 초기 총 자본금 (USDT)
        :param trade_amount: 1회 진입 시 투입할 금액 (USDT)
        :param fee_rate: 거래소 수수료율 (기본 0.1% - 바이낸스 현물 기준)
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance     # 현재 보유 현금 (USDT)
        self.trade_amount = trade_amount   # 1회 거래 대금
        self.fee_rate = fee_rate
        
        self.position_size = 0.0           # 현재 보유 중인 코인 수량
        self.entry_price = 0.0             # 진입 가격
        
        self.trades = []                   # 거래 내역 기록
        self.equity_curve = []             # 자산 변동 기록 (MDD 계산용)

    def run(self, df: pd.DataFrame):
        logger.info(f"📊 백테스팅 시작... (데이터 기간: {df['datetime'].iloc[0]} ~ {df['datetime'].iloc[-1]})")
        
        for index, row in df.iterrows():
            current_price = row['close']
            timestamp = row['datetime']
            
            # 1. 현재 총 자산 가치 기록 (현금 + 보유코인 가치)
            current_equity = self.balance + (self.position_size * current_price)
            self.equity_curve.append(current_equity)

            # 2. 매수 로직 (시그널 발생 & 포지션 없음 & 잔고 충분)
            if row['buy_signal'] == 1 and self.position_size == 0 and self.balance >= self.trade_amount:
                # 수수료 차감 후 실제 매수되는 코인 수량 계산
                fee = self.trade_amount * self.fee_rate
                invest_amount = self.trade_amount - fee
                
                self.position_size = invest_amount / current_price
                self.balance -= self.trade_amount
                self.entry_price = current_price
                self.entry_time = timestamp

            # 3. 매도 로직 (시그널 발생 & 포지션 보유 중)
            elif row['sell_signal'] == 1 and self.position_size > 0:
                # 매도 금액 계산 및 수수료 차감
                gross_revenue = self.position_size * current_price
                fee = gross_revenue * self.fee_rate
                net_revenue = gross_revenue - fee
                
                self.balance += net_revenue
                
                # 수익률 계산 (수수료 포함된 실제 수익률)
                profit_amount = net_revenue - self.trade_amount
                profit_pct = (profit_amount / self.trade_amount) * 100
                
                # 거래 내역 저장
                self.trades.append({
                    'entry_time': self.entry_time,
                    'exit_time': timestamp,
                    'entry_price': self.entry_price,
                    'exit_price': current_price,
                    'profit_pct': profit_pct,
                    'profit_amount': profit_amount
                })
                
                # 포지션 초기화
                self.position_size = 0.0

        # 백테스트 종료 후 남아있는 포지션이 있다면 마지막 종가로 강제 청산 (결과 평가를 위해)
        if self.position_size > 0:
            final_price = df['close'].iloc[-1]
            gross_revenue = self.position_size * final_price
            self.balance += (gross_revenue - (gross_revenue * self.fee_rate))
            self.equity_curve[-1] = self.balance # 마지막 자산 업데이트

        self._print_results()

    def _print_results(self):
        total_trades = len(self.trades)
        if total_trades == 0:
            logger.info("결과: 조건에 맞는 매매가 한 번도 발생하지 않았습니다.")
            return

        # 승률 계산
        winning_trades = [t for t in self.trades if t['profit_pct'] > 0]
        win_rate = (len(winning_trades) / total_trades) * 100

        # 총 수익률 계산
        total_return_pct = ((self.balance - self.initial_balance) / self.initial_balance) * 100

        # MDD (최대 낙폭) 계산
        equity_s = pd.Series(self.equity_curve)
        roll_max = equity_s.cummax()
        drawdown = equity_s / roll_max - 1.0
        mdd = drawdown.min() * 100

        logger.info("\n==============================================")
        logger.info("📈 백테스팅 결과 요약")
        logger.info("==============================================")
        logger.info(f"초기 자본금  : {self.initial_balance:,.2f} USDT")
        logger.info(f"최종 자본금  : {self.balance:,.2f} USDT")
        logger.info(f"총 수익률    : {total_return_pct:.2f}%")
        logger.info(f"총 매매 횟수 : {total_trades}회")
        logger.info(f"승률         : {win_rate:.2f}%")
        logger.info(f"최대 낙폭(MDD): {mdd:.2f}%")
        logger.info("==============================================\n")

if __name__ == "__main__":
    # 1. 데이터 가져오기 (예: 바이낸스 일봉 1000개 - 약 3년치 데이터)
    # 15분봉으로 1년치를 가져오려면 ccxt의 pagination 기능이 필요하므로, 
    # 우선 가장 많은 기간을 포괄할 수 있는 '1d'(일봉) 또는 '1h'(1시간봉)으로 1000개를 테스트합니다.
    fetcher = DataFetcher(exchange_id=Config.EXCHANGE_ID)
    
    # 테스트를 위해 1시간봉 1000개 (약 41일치) 데이터를 가져옵니다.
    print("거래소에서 과거 데이터를 수집 중입니다...")
    df_historical = fetcher.fetch_ohlcv(symbol=Config.SYMBOL, timeframe='1m', limit=1000)
    
    if df_historical is not None and not df_historical.empty:
        # 2. 전략을 통해 시그널 생성
        strategy = TradingStrategy()
        df_analyzed = strategy.analyze(df_historical)
        
        # 3. 백테스팅 실행
        backtester = Backtester(
            initial_balance=1000.0,     # 1000 USDT로 시작
            trade_amount=100.0,         # 1회 매매 시 100 USDT씩 투입
            fee_rate=0.001              # 바이낸스 현물 기본 수수료 0.1%
        )
        backtester.run(df_analyzed)
    else:
        print("데이터를 불러오지 못해 백테스팅을 종료합니다.")