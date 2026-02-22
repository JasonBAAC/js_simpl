"""
    Configuration module for the trading bot. This module defines the configuration settings for the bot, including API keys, trading parameters, and other settings that can be customized by the user.
    
"""

import os
from dotenv import load_dotenv
import ccxt

# Load environment variables from .env file
load_dotenv()

# Mock Trading 설정
IS_MOCK_TRADING = os.getenv('IS_MOCK_TRADING', 'True').lower() == 'true' not in ("false", "0", "no", "off")
MOCK_BALANCE = float(os.getenv('MOCK_BALANCE', '200000'))  # Mock balance for testing

def get_bithumb_client():
    """
    빗썸 API 클라이언트 생성
    
    Returns:
        ccxt.bithumb: 빗썸 거래소 인스턴스
    """
    
    api_key = os.getenv("BITHUMB_API_ACCESS_KEY")
    secret = os.getenv("BITHUMB_API_SECRET_KEY")
    
    if not api_key or not secret:
        raise ValueError("빗썸 API 키가 설정되지 않았습니다.")
    
    # ccxt 빗썸 클라이언트 생성
    exchange = ccxt.bithumb({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True  # API 호출 간격 제한 활성화
    })

    return exchange

if __name__ == "__main__":
    # 테스트: 빗썸 클라이언트 생성 및 잔액 조회
    print("Bithumb API connection test...")
        
    try:
        client = get_bithumb_client()
        print("API client created successfully.")
        
        asset = "XRP"
        ticker = client.fetch_ticker(f'{asset}/KRW')
        current_price = ticker['last']
        
        print(f"Current {asset}/KRW price: {current_price:,.0f} KRW")
        print(f"MOCK Trading Mode: {'Enabled' if IS_MOCK_TRADING else 'Disabled'}")
        print(f"MOCK Balance: {MOCK_BALANCE:,.0f} KRW")
        
        # balance = client.fetch_balance()
        # print("REAL Balance:", balance)
    except Exception as e:
        print("API 연결 실패:", str(e))

