# config.py
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    # ---------------------------------------------------------
    # 1. 보안 설정 (API Keys & Tokens) - .env에서 가져옴
    # ---------------------------------------------------------
    EXCHANGE_ID = os.getenv('EXCHANGE_ID', 'bithumb')  # 기본값은 'bithumb'로 설정
    QUOTE_CURRENCY = os.getenv('QUOTE_CURRENCY', 'KRW')  # 거래에 사용할 기준 화폐 (예: USDT, KRW)
    API_KEY = os.getenv('BITHUMB_API_ACCESS_KEY', '')
    SECRET_KEY = os.getenv('BITHUMB_API_SECRET_KEY', '')
    
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    

    # ---------------------------------------------------------
    # 2. 거래 기본 설정 (Trading Parameters)
    # ---------------------------------------------------------
    # SYMBOL = 'XRP/KRW'          # 거래할 페어
    TIMEFRAME = '1m'            # 캔들 타임프레임 (1m, 5m, 15m, 1h, 4h, 1d 등)
    TRADE_AMOUNT_USDT = 100.0    # 1회 매수 시 투입할 금액 (USDT 기준)
    
    MIN_PRICE = 1000
    MAX_PRICE = 1000000
    EVAL_HOURS = 2
    
    # ---------------------------------------------------------
    # 3. 봇 운영 설정 (Bot Operation Mode)
    # ---------------------------------------------------------
    DRY_RUN = True               # True: 페이퍼 트레이딩(가상 매매), False: 실전 매매
    CHECK_INTERVAL = 60          # 메인 루프 대기 시간 (초) - 1분마다 상태 확인
    MAX_RETRIES = 3              # API 호출 실패 시 최대 재시도 횟수

    # ---------------------------------------------------------
    # 4. 전략 세부 설정 (Strategy Parameters)
    # ---------------------------------------------------------
    # strategy.py 내부의 값을 밖으로 빼서 여기서 한 번에 관리할 수도 있습니다.
    EMA_SHORT = 20
    EMA_LONG = 50
    RSI_PERIOD = 14
    ADX_PERIOD = 14