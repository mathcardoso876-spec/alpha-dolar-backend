from .base_strategy import BaseStrategy
from ..config import BotConfig

class TestStrategy(BaseStrategy):
    """Estratégia de teste que sempre entra"""
    
    def __init__(self):
        super().__init__(name="Test Strategy - Always Trade")
        self.tick_count = 0
    
    def should_enter(self, tick_data):
        """Entra a cada 5 ticks alternando CALL/PUT"""
        self.update_tick(tick_data)
        self.tick_count += 1
        
        # Aguarda 3 ticks para ter dados
        if self.tick_count < 3:
            return False, None, 0.0
        
        # Entra a cada 5 ticks
        if self.tick_count % 5 == 0:
            direction = "CALL" if self.tick_count % 10 == 0 else "PUT"
            return True, direction, 0.95
        
        return False, None, 0.0
    
    def get_contract_params(self, direction):
        return {
            "contract_type": direction,
            "duration": 1,
            "duration_unit": "t",
            "symbol": BotConfig.DEFAULT_SYMBOL,
            "basis": BotConfig.BASIS
        }
