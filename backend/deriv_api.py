"""
Conexão com Deriv API via WebSocket
Alpha Dolar 2.0 - VERSÃO ULTRA ESTÁVEL COM AUTO-COMPRA
"""
import json
import time
import websocket
from datetime import datetime
import threading

# Import relativo correto
try:
    from .config import BotConfig
except ImportError:
    from config import BotConfig

class DerivAPI:
    """Gerencia conexão e comunicação com Deriv API"""

    def __init__(self, api_token=None):
        self.api_token = api_token or BotConfig.API_TOKEN
        self.app_id = BotConfig.APP_ID
        self.ws = None
        self.is_connected = False
        self.is_authorized = False
        self.account_info = {}
        self.balance = 0.0
        self.currency = "USD"

        # Callbacks
        self.on_tick_callback = None
        self.on_contract_callback = None
        self.on_balance_callback = None

        # Controle de reconexão
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 999
        self.should_reconnect = True

        # Thread de conexão e keep-alive
        self.ws_thread = None
        self.keep_alive_thread = None
        self.last_message_time = time.time()

    def log(self, message, level="INFO"):
        """Log formatado"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        emoji = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TRADE": "💰"
        }.get(level, "📝")
        print(f"[{timestamp}] {emoji} {message}")

    def _keep_alive_loop(self):
        """Thread que envia ping periodicamente"""
        while self.should_reconnect and self.ws:
            try:
                if self.is_connected:
                    # Envia ping a cada 5 segundos
                    self._send({"ping": 1})

                    # Verifica se não recebe mensagens há muito tempo
                    time_since_last = time.time() - self.last_message_time
                    if time_since_last > 30:
                        self.log("⚠️ Sem mensagens há 30s, reconectando...", "WARNING")
                        self._reconnect()

                time.sleep(5)
            except:
                pass

    def connect(self):
        """Conecta ao WebSocket da Deriv"""
        try:
            url = f"wss://ws.binaryws.com/websockets/v3?app_id={self.app_id}"
            self.log(f"Conectando à Deriv API...", "INFO")

            self.ws = websocket.WebSocketApp(
                url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            # Inicia conexão em thread separada
            self.ws_thread = threading.Thread(
                target=lambda: self.ws.run_forever(
                    ping_interval=0,
                    ping_timeout=None,
                    skip_utf8_validation=True
                )
            )
            self.ws_thread.daemon = True
            self.ws_thread.start()

            # Aguarda conexão
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if not self.is_connected:
                raise Exception("Timeout na conexão")

            # Inicia thread de keep-alive
            self.keep_alive_thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
            self.keep_alive_thread.start()

            return True

        except Exception as e:
            self.log(f"Erro ao conectar: {e}", "ERROR")
            return False

    def _reconnect(self):
        """Força reconexão"""
        try:
            self.log("🔄 Forçando reconexão...", "INFO")

            if self.ws:
                try:
                    self.ws.close()
                except:
                    pass

            self.is_connected = False
            self.is_authorized = False

            time.sleep(2)

            if self.connect():
                if self.authorize():
                    self.log("✅ Reconexão bem-sucedida!", "SUCCESS")

                    if hasattr(self, '_subscribed_symbol'):
                        self.subscribe_ticks(self._subscribed_symbol)
        except Exception as e:
            self.log(f"Erro na reconexão: {e}", "ERROR")

    def disconnect(self):
        """Desconecta do WebSocket"""
        self.should_reconnect = False
        if self.ws:
            self.ws.close()
            self.is_connected = False
            self.is_authorized = False
            self.log("Desconectado da Deriv API", "INFO")

    def authorize(self):
        """Autoriza conexão com token"""
        if not self.is_connected:
            self.log("Não conectado! Conecte primeiro.", "ERROR")
            return False

        try:
            self.log("Autorizando...", "INFO")
            auth_request = {
                "authorize": self.api_token
            }
            self._send(auth_request)

            timeout = 15
            start_time = time.time()
            while not self.is_authorized and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if not self.is_authorized:
                raise Exception("Timeout na autorização")

            self.log(f"✅ Autorizado! Saldo: ${self.balance:.2f} {self.currency}", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Erro na autorização: {e}", "ERROR")
            return False

    def subscribe_ticks(self, symbol):
        """Inscreve para receber ticks de um símbolo"""
        self._subscribed_symbol = symbol
        request = {
            "ticks": symbol,
            "subscribe": 1
        }
        self._send(request)
        self.log(f"Inscrito em ticks de {symbol}", "INFO")

    def subscribe_balance(self):
        """Inscreve para receber atualizações de saldo"""
        request = {
            "balance": 1,
            "subscribe": 1
        }
        self._send(request)

    def get_proposal(self, contract_type, symbol, amount, duration, duration_unit="t", barrier=None):
        """Obtém proposta de contrato"""
        proposal = {
            "proposal": 1,
            "amount": amount,
            "basis": BotConfig.BASIS,
            "contract_type": contract_type,
            "currency": self.currency,
            "duration": duration,
            "duration_unit": duration_unit,
            "symbol": symbol
        }

        if barrier is not None:
            proposal["barrier"] = str(barrier)

        self._send(proposal)
        self.log(f"Solicitando proposta: {contract_type} {symbol}", "INFO")

    def buy_contract(self, proposal_id, price):
        """Compra um contrato"""
        buy_request = {
            "buy": proposal_id,
            "price": price
        }
        self._send(buy_request)
        self.log(f"Comprando contrato ID: {proposal_id}", "TRADE")

    def sell_contract(self, contract_id, price=0):
        """Vende um contrato antes do vencimento"""
        sell_request = {
            "sell": contract_id,
            "price": price
        }
        self._send(sell_request)
        self.log(f"Vendendo contrato ID: {contract_id}", "TRADE")

    def get_contract_info(self, contract_id):
        """Obtém informações de um contrato"""
        request = {
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1
        }
        self._send(request)

    def _send(self, data):
        """Envia dados via WebSocket"""
        if self.ws and self.is_connected:
            try:
                message = json.dumps(data)
                self.ws.send(message)
            except Exception as e:
                self.log(f"Erro ao enviar: {e}", "ERROR")
                self._reconnect()
        else:
            self.log("WebSocket não conectado!", "ERROR")

    def _on_open(self, ws):
        """Callback quando conexão abre"""
        self.is_connected = True
        self.reconnect_attempts = 0
        self.last_message_time = time.time()
        self.log("Conexão WebSocket aberta", "SUCCESS")

    def _on_message(self, ws, message):
        """Callback quando recebe mensagem"""
        try:
            self.last_message_time = time.time()
            data = json.loads(message)
            msg_type = data.get("msg_type")

            # === PING/PONG ===
            if msg_type == "ping":
                self._send({"pong": 1})
                return

            # === AUTORIZAÇÃO ===
            if msg_type == "authorize":
                if "error" in data:
                    self.log(f"Erro na autorização: {data['error']['message']}", "ERROR")
                else:
                    self.is_authorized = True
                    auth_data = data.get("authorize", {})
                    self.account_info = auth_data
                    self.balance = float(auth_data.get("balance", 0))
                    self.currency = auth_data.get("currency", "USD")
                    self.subscribe_balance()

            # === SALDO ===
            elif msg_type == "balance":
                balance_data = data.get("balance", {})
                self.balance = float(balance_data.get("balance", 0))
                if self.on_balance_callback:
                    self.on_balance_callback(self.balance)

            # === TICK ===
            elif msg_type == "tick":
                tick_data = data.get("tick", {})
                if self.on_tick_callback:
                    self.on_tick_callback(tick_data)

            # === PROPOSTA ===
            elif msg_type == "proposal":
                if "error" in data:
                    self.log(f"Erro na proposta: {data['error']['message']}", "ERROR")
                else:
                    proposal = data.get("proposal", {})
                    proposal_id = proposal.get('id')
                    self.log(f"Proposta recebida: ID {proposal_id}", "INFO")

                    # ✅ AUTO-COMPRA!
                    price = proposal.get('ask_price')
                    if proposal_id and price:
                        self.log(f"🛒 Comprando automaticamente por ${price}", "TRADE")
                        self.buy_contract(proposal_id, price)

            # === COMPRA ===
            elif msg_type == "buy":
                if "error" in data:
                    self.log(f"Erro na compra: {data['error']['message']}", "ERROR")
                else:
                    buy_data = data.get("buy", {})
                    self.log(f"✅ Compra realizada! ID: {buy_data.get('contract_id')}", "SUCCESS")
                    self.get_contract_info(buy_data.get('contract_id'))

            # === CONTRATO ABERTO ===
            elif msg_type == "proposal_open_contract":
                contract = data.get("proposal_open_contract", {})
                if self.on_contract_callback:
                    self.on_contract_callback(contract)

                if contract.get("status") in ["won", "lost"]:
                    profit = float(contract.get("profit", 0))
                    status = "🎉 VITÓRIA" if contract.get("status") == "won" else "😞 DERROTA"
                    self.log(f"{status}! Lucro: ${profit:.2f}", "TRADE")

            # === VENDA ===
            elif msg_type == "sell":
                if "error" in data:
                    self.log(f"Erro na venda: {data['error']['message']}", "ERROR")
                else:
                    sell_data = data.get("sell", {})
                    self.log(f"✅ Venda realizada! Preço: ${sell_data.get('sold_for', 0)}", "SUCCESS")

        except json.JSONDecodeError:
            self.log(f"Erro ao decodificar mensagem: {message}", "ERROR")
        except Exception as e:
            self.log(f"Erro ao processar mensagem: {e}", "ERROR")

    def _on_error(self, ws, error):
        """Callback de erro"""
        self.log(f"Erro WebSocket: {error}", "ERROR")

    def _on_close(self, ws, close_status_code, close_msg):
        """Callback quando conexão fecha"""
        self.is_connected = False
        self.is_authorized = False
        self.log(f"Conexão fechada: {close_status_code} - {close_msg}", "WARNING")

        if self.should_reconnect:
            time.sleep(2)
            self._reconnect()

    def set_tick_callback(self, callback):
        """Define callback para receber ticks"""
        self.on_tick_callback = callback

    def set_contract_callback(self, callback):
        """Define callback para receber atualizações de contratos"""
        self.on_contract_callback = callback

    def set_balance_callback(self, callback):
        """Define callback para receber atualizações de saldo"""
        self.on_balance_callback = callback

# ===== TESTE =====
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 ALPHA DOLAR 2.0 - Teste com AUTO-COMPRA")
    print("="*60 + "\n")

    api = DerivAPI()

    def on_tick(tick):
        print(f"📈 Tick: {tick.get('quote')} - {tick.get('symbol')}")

    api.set_tick_callback(on_tick)

    if api.connect():
        if api.authorize():
            print(f"\n💰 Saldo: ${api.balance:.2f} {api.currency}")
            print(f"📧 Email: {api.account_info.get('email', 'N/A')}")

            api.subscribe_ticks("R_100")

            print("\n⏳ Recebendo ticks por 60 segundos...\n")
            time.sleep(60)

            api.disconnect()
        else:
            print("❌ Falha na autorização")
    else:
        print("❌ Falha na conexão")
