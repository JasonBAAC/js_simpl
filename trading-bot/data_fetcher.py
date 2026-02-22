import ccxt
import pandas as pd
import logging
import time

# 로깅 설정 (오류 발생 시 원인 파악을 위해 필수)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, exchange_id='bithumb'):
        """
        거래소 객체를 초기화합니다. 
        여기서는 데이터만 조회하므로 API 키가 필요 없습니다.
        """
        try:
            # 입력받은 exchange_id 문자열로 ccxt 거래소 객체 동적 생성
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,  # 봇이 거래소 IP 밴을 당하지 않도록 자체 속도 조절
                'options': {
                    'defaultType': 'future'  # 선물 거래 데이터가 필요하다면 'future', 현물은 'spot'
                }
            })
            logger.info(f"{exchange_id.capitalize()} 거래소 연결 준비 완료.")
        except AttributeError:
            logger.error(f"지원하지 않는 거래소입니다: {exchange_id}")
            raise

    def fetch_ohlcv(self, symbol, timeframe='1m', limit=500, max_retries=3):
        """
        특정 코인의 OHLCV 데이터를 가져와 DataFrame으로 반환합니다.
        네트워크 오류를 대비해 재시도(Retry) 로직을 포함합니다.
        """
        for attempt in range(max_retries):
            try:
                # ccxt를 통해 과거 캔들 데이터 수집
                raw_data = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                
                # 수집한 데이터를 pandas DataFrame으로 변환
                df = self._preprocess_data(raw_data)
                logger.info(f"{symbol} ({timeframe}) 데이터 {len(df)}개 수집 완료.")
                return df
                
            except ccxt.NetworkError as e:
                logger.warning(f"네트워크 오류 (재시도 {attempt+1}/{max_retries}): {e}")
                time.sleep(2)  # 2초 대기 후 재시도
            except ccxt.ExchangeError as e:
                logger.error(f"거래소 오류: {e}")
                break
            except Exception as e:
                logger.error(f"알 수 없는 오류 발생: {e}")
                break
                
        return None  # 실패 시 None 반환
    
    def fetch_filtered_symbols(self, quote='KRW', min_price=1000, max_price=30000):
        """
        1차 필터링: 지정된 마켓(KRW)에서 가격대 조건에 맞는 심볼 리스트만 추출합니다.
        (모든 코인의 OHLCV를 다 가져오면 API 호출 제한에 걸리므로 현재가로 먼저 거릅니다.)
        """
        tickers = self.exchange.fetch_tickers()
        filtered_symbols = []
        
        for symbol, ticker in tickers.items():
            # KRW 마켓인지 확인 (예: 'XRP/KRW')
            if symbol.endswith(f'/{quote}'):
                current_price = ticker.get('last', 0)
                # 가격 조건 확인
                if current_price and (min_price <= current_price <= max_price):
                    filtered_symbols.append(symbol)
                    
        return filtered_symbols
    
    
    def _preprocess_data(self, raw_data):
        """
        ccxt에서 받은 원시 리스트 데이터를 Pandas DataFrame으로 예쁘게 가공합니다.
        (내부에서만 사용하는 메서드이므로 이름 앞에 '_'를 붙였습니다.)
        """
        # 1. 컬럼 이름 지정
        df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 2. 숫자형 데이터 타입 확실히 지정 (지표 계산 시 오류 방지)
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
        
        # 3. 사람이 읽기 쉬운 datetime(UTC 기준) 컬럼 추가
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        
        return df

# --- 테스트 코드 (이 파일을 직접 실행했을 때만 동작) ---
if __name__ == "__main__":
    # Binance 거래소에서 BTC/USDT 1시간봉 데이터 100개를 가져오는 테스트
    fetcher = DataFetcher(exchange_id='bithumb')
    df_btc = fetcher.fetch_ohlcv(symbol='XRP/KRW', timeframe='1m', limit=200)
    
    if df_btc is not None:
        print("\n최근 5개 캔들 데이터:")
        print(df_btc.tail(10)) # 가장 최근 데이터 5개 출력