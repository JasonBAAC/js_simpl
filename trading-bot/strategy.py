import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self):
        """
        전략 초기화. 
        필요한 파라미터(예: RSI 기간, EMA 기간 등)를 여기서 정의할 수 있습니다.
        """
        self.ema_short_period = 20
        self.ema_long_period = 50
        self.rsi_period = 14
        self.adx_period = 14
        self.atr_period = 14

    def populate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        데이터프레임에 기술적 지표(RSI, EMA, ADX, ATR)를 추가합니다.
        """
        try:
            # 1. EMA (지수이동평균선) - 단기/장기 추세 확인
            df['ema_short'] = ta.ema(df['close'], length=self.ema_short_period)
            df['ema_long'] = ta.ema(df['close'], length=self.ema_long_period)

            # 2. RSI (상대강도지수) - 과매수/과매도 판단
            df['rsi'] = ta.rsi(df['close'], length=self.rsi_period)

            # 3. ADX (평균방향지수) - 추세의 강도 확인
            # pandas_ta의 adx는 ADX, DMP(+DI), DMN(-DI) 3개 컬럼을 반환하므로 ADX만 추출
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=self.adx_period)
            df['adx'] = adx_df[f'ADX_{self.adx_period}']

            # 4. ATR (평균진폭) - 변동성 확인 (손절/익절 기준에 활용)
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=self.atr_period)

            # 지표 계산 초반의 NaN(결측치) 값 제거
            df.dropna(inplace=True)
            
            return df

        except Exception as e:
            logger.error(f"지표 계산 중 오류 발생: {e}")
            return df

    def populate_entry_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        매수(Long) 조건을 정의하고 시그널을 생성합니다.
        """
        # 기본 시그널 컬럼 0으로 초기화
        df['buy_signal'] = 0

        # --- [매수 전략 예시] ---
        # 1. 단기 EMA가 장기 EMA 위에 있음 (상승 추세)
        # 2. ADX가 25 이상 (강한 추세장)
        # 3. RSI가 40 이하 (상승 추세 속 단기 눌림목/과매도)
        
        buy_condition = (
            (df['ema_short'] > df['ema_long']) & 
            (df['adx'] > 25) & 
            (df['rsi'] < 40)
        )

        # 조건이 맞는 행의 'buy_signal'을 1로 변경
        df.loc[buy_condition, 'buy_signal'] = 1
        
        return df

    def populate_exit_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        매도(Exit/Short) 조건을 정의하고 시그널을 생성합니다.
        """
        df['sell_signal'] = 0

        # --- [매도 전략 예시] ---
        # 1. RSI가 70 이상 (과매수 구간 도달)
        # 2. 또는 단기 EMA가 장기 EMA 아래로 데드크로스 발생 시
        
        sell_condition = (
            (df['rsi'] > 70) | 
            (df['ema_short'] < df['ema_long'])
        )

        df.loc[sell_condition, 'sell_signal'] = 1
        
        return df

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        위의 3개 함수를 순차적으로 실행하여 최종 데이터프레임을 반환하는 래퍼(Wrapper) 함수
        """
        df = self.populate_indicators(df)
        df = self.populate_entry_signals(df)
        df = self.populate_exit_signals(df)
        return df

    def populate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # (기존 RSI, EMA 지표 등 유지) ...
        
        # EMV 지표 추가 (고가, 저가, 거래량이 모두 필요함)
        df['emv'] = ta.eom(df['high'], df['low'], df['volume'], length=14)
        return df

    def get_performance_score(self, df: pd.DataFrame, eval_hours: int) -> float:
        """
        최근 N시간 동안의 RSI와 EMV를 바탕으로 코인의 매력도 점수를 계산합니다.
        """
        # 1시간봉 기준이면 최근 2개 캔들, 15분봉이면 최근 8개 캔들 추출
        # (타임프레임에 맞춰 eval_candles 개수 조정 필요)
        recent_df = df.tail(eval_hours) 
        
        # 예시 평가 로직: 
        # 최근 EMV의 평균이 양수(쉽게 상승중)이고, RSI가 너무 과매수가 아닌(70 이하) 경우 점수 부여
        avg_emv = recent_df['emv'].mean()
        avg_rsi = recent_df['rsi'].mean()
        
        if avg_rsi > 70:
            return -100 # 과매수는 배제
            
        # EMV 값이 높을수록, RSI가 40~60 사이에서 안정적일수록 가산점
        score = avg_emv * (1 if 40 <= avg_rsi <= 60 else 0.5)
        return float(score)



# --- 테스트 코드 ---
if __name__ == "__main__":
    # data_fetcher 모듈이 있다고 가정하고 가상의 데이터프레임을 생성하여 테스트합니다.
    # 실제 환경에서는 data_fetcher.fetch_ohlcv() 의 결과를 넣습니다.
    
    print("가상 데이터로 전략 모듈 테스트를 진행합니다...")
    # 임의의 가격 데이터 생성 (100개)
    np.random.seed(42)
    dummy_data = {
        'timestamp': pd.date_range(start='2026-01-01', periods=100, freq='1min'),
        'open': np.random.uniform(20000, 21000, 100),
        'high': np.random.uniform(20500, 21500, 100),
        'low': np.random.uniform(19500, 20500, 100),
        'close': np.random.uniform(20000, 21000, 100),
        'volume': np.random.uniform(10, 100, 100)
    }
    df_mock = pd.DataFrame(dummy_data)
    
    strategy = TradingStrategy()
    df_result = strategy.analyze(df_mock)
    
    print("\n[최종 생성된 데이터프레임 (최근 10개)]")
    # 시그널과 주요 지표만 출력
    print(df_result[['timestamp', 'close', 'rsi', 'adx', 'buy_signal', 'sell_signal']].tail(10))