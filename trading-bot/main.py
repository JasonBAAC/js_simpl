import time
import logging
import requests
import traceback

# 앞서 만든 모듈들을 불러옵니다.
from data_fetcher import DataFetcher
from strategy import TradingStrategy
from executor import OrderExecutor
from config import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# 봇 설정 (실제 환경에서는 config.py나 .env로 분리하는 것이 좋습니다)
# ==========================================
EXCHANGE_ID = 'bithumb'
API_KEY = 'YOUR_API_KEY'
SECRET_KEY = 'YOUR_SECRET_KEY'

TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'

SYMBOL = 'XRP/KRW'
TIMEFRAME = '1m'       # 15분봉 사용
TRADE_AMOUNT_USDT = 100 # 1회 매수 시 투입할 금액 (USDT)
DRY_RUN = True          # True: 가상 매매, False: 실전 매매
CHECK_INTERVAL = 60     # 루프 대기 시간 (초) - 1분마다 확인

# ==========================================

def send_telegram_message(message: str):
    """
    텔레그램 봇 API를 이용하여 메시지를 전송합니다.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("텔레그램 설정이 비어있어 메시지를 전송하지 않습니다.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"텔레그램 메시지 전송 실패: {e}")

def run_bot():
    current_holding_symbol = None # 현재 보유 중인 코인 (없으면 None)
    
    while True:
        if current_holding_symbol is None:
            # === [1단계: 종목 탐색 및 매수] ===
            # 1. 가격대(1000~30000원)에 맞는 코인 리스트업
            candidate_symbols = fetcher.fetch_filtered_symbols('KRW', 1000, 30000)
            
            best_symbol = None
            best_score = -9999
            
            # 2. 각 후보 코인의 OHLCV를 가져와 EMV/RSI 퍼포먼스 점수 계산
            for sym in candidate_symbols:
                df = fetcher.fetch_ohlcv(sym)
                df = strategy.populate_indicators(df)
                score = strategy.get_performance_score(df, eval_hours=2)
                
                if score > best_score:
                    best_score = score
                    best_symbol = sym
            
            # 3. 가장 점수가 높은 코인 매수
            if best_symbol and best_score > 0: # 최소 기준 점수 이상일 때만
                executor.execute_trade(best_symbol, 'buy', ...)
                current_holding_symbol = best_symbol
                
        else:
            # === [2단계: 보유 종목 감시 및 매도] ===
            # 1. 현재 들고 있는 코인의 데이터만 가져옴
            df = fetcher.fetch_ohlcv(current_holding_symbol)
            df = strategy.analyze(df)
            
            # 2. 매도 시그널 확인
            if df.iloc[-2]['sell_signal'] == 1:
                executor.execute_trade(current_holding_symbol, 'sell', ...)
                current_holding_symbol = None # 포지션 비움 -> 다음 사이클에 다시 스캔 시작

        # 다음 사이클까지 대기
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_bot()