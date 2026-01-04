"""
Classe Base para todas as estratégias
Alpha Dolar 2.0
"""
from abc import ABC, abstractmethod
from datetime import datetime
from collections import deque

class BaseStrategy(ABC):
    """
    Classe base abstrata para estratégias de trading
    Todas as estratégias devem herdar desta classe
    """

    def __init__(self, name="Base Strategy"):
        self.name = name
        self.ticks_history = deque(maxlen=100)  # Histórico de ticks
        self.candles_history = deque(maxlen=50)  # Histórico de candles
        self.last_signal = None
        self.signal_count = 0

    @abstractmethod
    def should_enter(self, tick_data):
        """
        Decide se deve entrar em um trade

        Args:
            tick_data (dict): Dados do tick atual

        Returns:
            tuple: (should_enter: bool, direction: str, confidence: float)
                   direction: "CALL" ou "PUT"
                   confidence: 0.0 a 1.0
        """
        pass

    @abstractmethod
    def get_contract_params(self, direction):
        """
        Retorna parâmetros do contrato

        Args:
            direction (str): "CALL" ou "PUT"

        Returns:
            dict: Parâmetros do contrato
        """
        pass

    def update_tick(self, tick_data):
        """
        Atualiza histórico com novo tick

        Args:
            tick_data (dict): Dados do tick
        """
        self.ticks_history.append({
            'quote': float(tick_data.get('quote', 0)),
            'epoch': tick_data.get('epoch'),
            'symbol': tick_data.get('symbol'),
            'timestamp': datetime.now()
        })

    def get_last_ticks(self, n=10):
        """
        Retorna os últimos N ticks

        Args:
            n (int): Quantidade de ticks

        Returns:
            list: Lista com últimos N ticks
        """
        return list(self.ticks_history)[-n:]

    def get_tick_prices(self, n=10):
        """
        Retorna apenas os preços dos últimos N ticks

        Args:
            n (int): Quantidade de ticks

        Returns:
            list: Lista com preços
        """
        ticks = self.get_last_ticks(n)
        return [tick['quote'] for tick in ticks]

    def get_last_digits(self, n=10):
        """
        Retorna últimos dígitos dos preços

        Args:
            n (int): Quantidade de dígitos

        Returns:
            list: Lista com últimos dígitos (0-9)
        """
        prices = self.get_tick_prices(n)
        return [int(str(price).split('.')[-1][-1]) for price in prices]

    def calculate_trend(self, n=10):
        """
        Calcula tendência baseado nos últimos N ticks

        Args:
            n (int): Quantidade de ticks para análise

        Returns:
            str: "UP", "DOWN" ou "SIDEWAYS"
        """
        prices = self.get_tick_prices(n)

        if len(prices) < 2:
            return "SIDEWAYS"

        # Conta quantos ticks subiram vs desceram
        ups = 0
        downs = 0

        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                ups += 1
            elif prices[i] < prices[i-1]:
                downs += 1

        # Tendência clara precisa de pelo menos 60% em uma direção
        threshold = 0.6
        total = ups + downs

        if total == 0:
            return "SIDEWAYS"

        if ups / total > threshold:
            return "UP"
        elif downs / total > threshold:
            return "DOWN"
        else:
            return "SIDEWAYS"

    def calculate_volatility(self, n=10):
        """
        Calcula volatilidade simples

        Args:
            n (int): Quantidade de ticks

        Returns:
            float: Volatilidade (desvio padrão)
        """
        prices = self.get_tick_prices(n)

        if len(prices) < 2:
            return 0.0

        # Calcula desvio padrão
        mean = sum(prices) / len(prices)
        variance = sum((x - mean) ** 2 for x in prices) / len(prices)
        return variance ** 0.5

    def detect_pattern(self, pattern_type="consecutive"):
        """
        Detecta padrões nos últimos ticks

        Args:
            pattern_type (str): Tipo de padrão a detectar

        Returns:
            dict: Informações do padrão detectado
        """
        prices = self.get_tick_prices(10)

        if len(prices) < 3:
            return {"detected": False}

        if pattern_type == "consecutive":
            # Detecta quantos ticks consecutivos na mesma direção
            consecutive_ups = 0
            consecutive_downs = 0

            for i in range(1, len(prices)):
                if prices[i] > prices[i-1]:
                    consecutive_ups += 1
                    consecutive_downs = 0
                elif prices[i] < prices[i-1]:
                    consecutive_downs += 1
                    consecutive_ups = 0
                else:
                    consecutive_ups = 0
                    consecutive_downs = 0

            return {
                "detected": True,
                "consecutive_ups": consecutive_ups,
                "consecutive_downs": consecutive_downs
            }

        return {"detected": False}

    def get_sma(self, n=10):
        """
        Calcula Média Móvel Simples

        Args:
            n (int): Período

        Returns:
            float: SMA
        """
        prices = self.get_tick_prices(n)

        if len(prices) < n:
            return None

        return sum(prices) / len(prices)

    def get_ema(self, n=10, smoothing=2):
        """
        Calcula Média Móvel Exponencial

        Args:
            n (int): Período
            smoothing (int): Fator de suavização

        Returns:
            float: EMA
        """
        prices = self.get_tick_prices(n)

        if len(prices) < n:
            return None

        # Calcula EMA
        multiplier = smoothing / (1 + n)
        ema = prices[0]  # Começa com o primeiro preço

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def is_ready(self):
        """
        Verifica se a estratégia tem dados suficientes

        Returns:
            bool: True se pronta para operar
        """
        return len(self.ticks_history) >= 10

    def reset(self):
        """Reset da estratégia"""
        self.ticks_history.clear()
        self.candles_history.clear()
        self.last_signal = None
        self.signal_count = 0

    def get_info(self):
        """
        Retorna informações da estratégia

        Returns:
            dict: Informações
        """
        return {
            "name": self.name,
            "ticks_count": len(self.ticks_history),
            "is_ready": self.is_ready(),
            "last_signal": self.last_signal,
            "signal_count": self.signal_count
        }

    def __str__(self):
        return f"Strategy: {self.name}"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

# ===== TESTE =====
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTE DA CLASSE BASE STRATEGY")
    print("="*60 + "\n")

    # Como BaseStrategy é abstrata, vamos criar uma implementação simples para teste
    class SimpleStrategy(BaseStrategy):
        """Estratégia simples para teste"""

        def should_enter(self, tick_data):
            # Lógica simples: entra se tendência é clara
            trend = self.calculate_trend(5)

            if trend == "UP":
                return True, "CALL", 0.7
            elif trend == "DOWN":
                return True, "PUT", 0.7
            else:
                return False, None, 0.0

        def get_contract_params(self, direction):
            return {
                "contract_type": direction,
                "duration": 1,
                "duration_unit": "t",
                "symbol": "R_100"
            }

    # Cria estratégia
    strategy = SimpleStrategy("Test Strategy")
    print(f"📊 Estratégia criada: {strategy}")
    print(f"   Pronta para operar: {strategy.is_ready()}\n")

    # Simula ticks
    print("📈 Simulando ticks:")
    simulated_ticks = [
        {"quote": 100.50, "symbol": "R_100", "epoch": 1},
        {"quote": 100.55, "symbol": "R_100", "epoch": 2},
        {"quote": 100.60, "symbol": "R_100", "epoch": 3},
        {"quote": 100.65, "symbol": "R_100", "epoch": 4},
        {"quote": 100.70, "symbol": "R_100", "epoch": 5},
        {"quote": 100.75, "symbol": "R_100", "epoch": 6},
        {"quote": 100.72, "symbol": "R_100", "epoch": 7},
        {"quote": 100.68, "symbol": "R_100", "epoch": 8},
        {"quote": 100.64, "symbol": "R_100", "epoch": 9},
        {"quote": 100.60, "symbol": "R_100", "epoch": 10},
    ]

    for tick in simulated_ticks:
        strategy.update_tick(tick)
        print(f"   Tick: {tick['quote']}")

    print(f"\n   Pronta agora: {strategy.is_ready()}")

    # Testa métodos
    print("\n📊 ANÁLISES:")
    print(f"   Últimos 5 preços: {strategy.get_tick_prices(5)}")
    print(f"   Tendência: {strategy.calculate_trend(5)}")
    print(f"   Volatilidade: {strategy.calculate_volatility(5):.4f}")
    print(f"   SMA(5): {strategy.get_sma(5):.2f}")
    print(f"   EMA(5): {strategy.get_ema(5):.2f}")

    # Testa sinal
    print("\n🎯 TESTE DE SINAL:")
    should_enter, direction, confidence = strategy.should_enter(simulated_ticks[-1])
    print(f"   Deve entrar: {should_enter}")
    print(f"   Direção: {direction}")
    print(f"   Confiança: {confidence:.1%}")

    if should_enter:
        params = strategy.get_contract_params(direction)
        print(f"   Parâmetros: {params}")

    print("\n")
