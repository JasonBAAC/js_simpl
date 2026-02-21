"""
빗썸에서 BTC/KRW OHLCV 데이터를 가져오고 기술적 지표를 계산합니다.
"""

import time
import pandas as pd
from ccxt import Exchange

SYMBOL = 'BTC/KRW'
TIMEFRAME = '1m'
DEFAULT_LIMIT = 200

def get_ohlcv_data(exchange: Exchange, limit: int = DEFAULT_LIMIT):
    """
    빗썸에서 OHLCV 데이터를 가져옵니다.
    
    Args:
        exchange (Exchange): ccxt 거래소 인스턴스
        symbol (str): 거래쌍 (예: 'XRP/KRW')
        timeframe (str): 시간 프레임 (예: '1m', '5m', '1h')
        limit (int): 가져올 데이터 수
    
    Returns:
        pd.DataFrame: OHLCV 데이터프레임
    """
    try:
        ohlcv = exchange.fetch_ohlcv(
            SYMBOL, 
            timeframe=TIMEFRAME, 
            limit=limit
        )
        
        df = pd.DataFrame(
            ohlcv, 
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        
        return df
    
    except Exception as e:
        print(f"데이터 가져오기 실패: {str(e)}")
        return pd.DataFrame()

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index) 계산
    
    Args:
        close (pd.Series): 종가 시리즈
        period (int): RSI 계산 기간
    
    Returns:
        pd.Series: RSI 값 시리즈 (1~100)
    """
    
    # 가격 변화량 계산
    delta = close.diff()
    
    # 상승과 하락 분리
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Wilder's Smoothing 방법으로 평균 계산
    alpha = 1.0 / period
    avg_gain = gain.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    
    # RS (Relative Strength) 계산
    rs = avg_gain / avg_loss.replace(0, float('inf'))  # 0으로 나누는 경우를 방지
    
    # RSI 계산
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_ema(close: pd.Series, period: int = 20) -> pd.Series:
    """
    EMA (Exponential Moving Average) 계산
    
    Args:
        close (pd.Series): 종가 시리즈
        period (int): EMA 계산 기간 (예: 20, 60)
    
    Returns:
        pd.Series: EMA 값 시리즈
    """
    
    ema = close.ewm(span=period, adjust=False).mean()
    
    return ema

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ATR (Average True Range) 계산
    
    Args:
        df (pd.DataFrame): OHLCV 데이터프레임 (열: 'high', 'low', 'close')
        period (int): ATR 계산 기간
    
    Returns:
        pd.Series: ATR 값 시리즈
    """
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range 계산 - 세 가지 방법 중 최대값을 사용
    tr1 = high - low
    tr2 = (close.shift(1) - high).abs()
    tr3 = (close.shift(1) - low).abs()
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Wilder's Smoothing 방법으로 ATR 계산 (ATR은 True Range의 지수 이동 평균)
    alpha = 1.0 / period
    atr = true_range.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    
    return atr

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ADX (Average Directional Index) 계산
    
    Args:
        df (pd.DataFrame): OHLCV 데이터프레임 (열: 'high', 'low', 'close')
        period (int): ADX 계산 기간
    
    Returns:
        pd.Series: ADX 값 시리즈
    """
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # 방향성 지표 계산 (+DM, -DM)
    
    # up_move = high.diff()
    # down_move = low.diff()
    # plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    # minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # True Range 계산
    # tr1 = high - low
    # tr2 = (close.shift(1) - high).abs()
    # tr3 = (close.shift(1) - low).abs()
    # true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR 재사용
    atr = calculate_atr(df, period)
    
    
    # Wilder's Smoothing 방법으로 평균 계산 (+DI, -DI)
    alpha = 1.0 / period
    plus_di = 100 * (plus_dm.ewm(alpha=alpha, adjust=False, min_periods=period).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=alpha, adjust=False, min_periods=period).mean() / atr)
    
    # ADX 계산
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float('inf')) * 100
    adx = dx.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
    
    return adx

def get_ohlcv_with_indicators(exchange: Exchange, limit: int = 200) -> pd.DataFrame:
    
    """
    OHLCV 데이터와 기술적 지표를 함께 가져옵니다.
    
    Args:
        exchange (Exchange): ccxt 거래소 인스턴스
        symbol (str): 거래쌍 (예: 'XRP/KRW')
        timeframe (str): 시간 프레임 (예: '1m', '5m', '1h')
        limit (int): 가져올 데이터 수
    
    Returns:
        pd.DataFrame: 
            - timestamp, open, high, low, close, volume 
            - rsi_14, ema_20, ema_60, atr_14, adx_14
    """
    
    # 1 OHLCV 데이터 수집
    df = get_ohlcv_data(exchange, limit)
    
    if df.empty:
        return df
        
    # 2 기술적 지표 계산
    df['rsi_14'] = calculate_rsi(df['close'], period=14)
    df['ema_20'] = calculate_ema(df['close'], period=20)
    df['ema_60'] = calculate_ema(df['close'], period=60)
    df['atr_14'] = calculate_atr(df, period=14) 
    df['adx_14'] = calculate_adx(df, period=14)
        
    return df
    


if __name__ == "__main__":
    from config import get_bithumb_client
    
    # print("Fetching OHLCV data...")
    print("=" * 60)
    print("Fetching OHLCV data with indicators...")
    print("=" * 60)
    
    
    exchange = get_bithumb_client()

    # df = get_ohlcv_data(exchange, limit = 10)
    
    # print(f"\n Fetched {len(df)} rows of OHLCV data")
    # print("\n latest 5 rows:")
    # print(df.tail())

    df = get_ohlcv_with_indicators(exchange, limit = 200)
    
    # 최신 데이터 출력
    latest = df.iloc[-1]
    
    print(f"\nLatest data for {SYMBOL} ({TIMEFRAME}):")
    print(f"Timestamp: {latest['timestamp']}")
    print(f"Close: {latest['close']:,.0f} KRW")
    print(f"RSI_14: {latest['rsi_14']:.2f} ")
    print(f"EMA_20: {latest['ema_20']:,.0f} KRW")
    print(f"EMA_60: {latest['ema_60']:,.0f} KRW")
    print(f"ATR_14: {latest['atr_14']:,.0f} KRW")
    print(f"ADX_14: {latest['adx_14']:.2f}")
    
    # 추세판단
    if latest['ema_20'] > latest['ema_60']:
        print("\n추세: 정배열(상승 추세)")
    else: 
        print("\n추세: 역배열(하락 추세)")
        
    # RSI 과매수/과매도 판단
    if latest['rsi_14'] < 30:
        print("RSI: 과매도 구간")
    elif latest['rsi_14'] > 70:
        print("RSI: 과매수 구간")
    else:
        print("RSI: 중립 구간")

    # ADX가 25 이상이면 추세가 강하다고 판단
    if latest['adx_14'] > 25:
        print("ADX: 강한 추세")
    else:
        print("ADX: 약한 추세")
    

    df.to_csv("market_data.csv", index=False)
    
