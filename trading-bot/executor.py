import ccxt
import logging
import time

logger = logging.getLogger(__name__)

class OrderExecutor:
    def __init__(self, exchange_id, api_key, secret_key, dry_run=True):
        """
        주문 실행 객체 초기화.
        실제 거래를 위해 API Key와 Secret Key가 필요합니다.
        dry_run=True일 경우 실제 주문은 들어가지 않고 로그만 찍힙니다.
        """
        self.dry_run = dry_run
        self.exchange_id = exchange_id

        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'  # 현물(spot) 거래 기준. 선물은 'future'
                }
            })
            
            # 연결 테스트를 위해 거래소 서버 시간 로드
            self.exchange.load_markets()
            mode = "🟢 페이퍼 트레이딩(Dry Run)" if self.dry_run else "🔴 실전 매매(Live)"
            logger.info(f"{exchange_id.capitalize()} 거래소 실행 모듈 연결 완료. 모드: {mode}")
            
        except Exception as e:
            logger.error(f"거래소 초기화 실패. API 키를 확인하세요: {e}")
            raise

    def get_free_balance(self, currency: str) -> float:
        """
        특정 코인(또는 법정화폐/USDT)의 '사용 가능한' 잔고를 조회합니다.
        """
        if self.dry_run:
            # 페이퍼 트레이딩일 경우 임의의 가상 잔고 반환
            virtual_balances = {'USDT': 1000.0, 'BTC': 0.1}
            return virtual_balances.get(currency, 0.0)

        try:
            balance = self.exchange.fetch_balance()
            # currency(예: 'USDT')의 free(사용 가능) 잔고 반환
            free_balance = balance.get(currency, {}).get('free', 0.0)
            return float(free_balance)
        except Exception as e:
            logger.error(f"잔고 조회 중 오류 발생 ({currency}): {e}")
            return 0.0

    def execute_trade(self, symbol: str, side: str, amount: float, current_price: float):
        """
        매수(buy) 또는 매도(sell) 주문을 실행합니다.
        side: 'buy' 또는 'sell'
        amount: 거래할 코인의 수량 (예: 0.01 BTC)
        current_price: 현재가 (로그 출력 및 가상 매매 기록용)
        """
        order_type = 'market'  # 시장가 주문을 기본으로 설정 (지정가 'limit'도 가능)
        
        logger.info(f"주문 요청: {side.upper()} {amount} {symbol} (현재가: 약 {current_price})")

        # 1. 페이퍼 트레이딩 (Dry Run) 모드일 경우
        if self.dry_run:
            logger.info(f"[DRY RUN] 가상 주문 체결 완료: {side.upper()} {amount} {symbol}")
            return {
                'status': 'closed', 
                'side': side, 
                'amount': amount, 
                'price': current_price,
                'info': 'This is a dry run mock order'
            }

        # 2. 실전 매매 (Live) 모드일 경우
        try:
            # ccxt를 이용한 실제 주문 실행
            order_result = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount
            )
            logger.info(f"✅ 실전 주문 체결 성공: {order_result['id']}")
            return order_result

        except ccxt.InsufficientFunds as e:
            logger.error(f"❌ 잔고 부족: {e}")
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ 잘못된 주문 (최소 주문 수량 미달 등): {e}")
        except Exception as e:
            logger.error(f"❌ 주문 실행 중 알 수 없는 오류 발생: {e}")
        
        return None

# --- 테스트 코드 ---
if __name__ == "__main__":
    # 보안상 API 키는 하드코딩하지 않고 환경변수나 config에서 불러와야 합니다.
    # 여기서는 테스트를 위해 빈 문자열을 넣고 dry_run=True로 실행합니다.
    API_KEY = ""
    SECRET_KEY = ""
    
    executor = OrderExecutor(
        exchange_id='binance', 
        api_key=API_KEY, 
        secret_key=SECRET_KEY, 
        dry_run=True  # ❗ 반드시 True로 먼저 테스트하세요
    )
    
    # 1. 잔고 조회 테스트
    usdt_balance = executor.get_free_balance('USDT')
    print(f"\n현재 사용 가능한 USDT 잔고: {usdt_balance}")
    
    # 2. 가상 매수 주문 테스트 (비트코인이 50,000 USDT라고 가정할 때 100 USDT 어치 매수)
    current_btc_price = 50000.0
    invest_usdt = 100.0
    buy_amount = invest_usdt / current_btc_price  # 살 수 있는 BTC 수량 계산
    
    executor.execute_trade(
        symbol='BTC/USDT', 
        side='buy', 
        amount=buy_amount, 
        current_price=current_btc_price
    )