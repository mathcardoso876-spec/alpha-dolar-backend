"""
Alpha Bot Balanced - Estratégia Intermediária
Balanceada entre velocidade e precisão
Win Rate esperado: 55-60%
Frequência: 2-5 trades/hora
"""
from .base_strategy import BaseStrategy
from ..config import BotConfig
import statistics

class AlphaBotBalanced(BaseStrategy):
    """Estratégia balanceada - nem muito lenta, nem muito agressiva"""
    
    def __init__(self):
        super().__init__(name="Alpha Bot Balanced")
        self.min_history = 20
        self.last_signal_tick = 0
        self.cooldown_ticks = 15
        self.total_ticks_received = 0
    
    def should_enter(self, tick_data):
        """
        Estratégia baseada em:
        - Momentum de curto prazo (últimos 10 ticks)
        - Reversão à média
        - Volatilidade forte
        """
        self.update_tick(tick_data)
        self.total_ticks_received += 1
        
        print(f"[DEBUG] should_enter chamado! Histórico: {len(self.ticks_history)}/{self.min_history}, Total ticks: {self.total_ticks_received}")
        
        if len(self.ticks_history) < self.min_history:
            print(f"[DEBUG] Aguardando histórico completo...")
            return False, None, 0.0
        
        ticks_since_last = self.total_ticks_received - self.last_signal_tick
        if ticks_since_last < self.cooldown_ticks:
            print(f"[DEBUG] Cooldown ativo: {ticks_since_last}/{self.cooldown_ticks} ticks")
            return False, None, 0.0
        
        try:
            recent_10 = [tick['quote'] if isinstance(tick, dict) else tick for tick in list(self.ticks_history)[-10:]]
            recent_20 = [tick['quote'] if isinstance(tick, dict) else tick for tick in list(self.ticks_history)[-20:]]
            
            current_price = recent_10[-1]
            
            ma_10 = statistics.mean(recent_10)
            ma_20 = statistics.mean(recent_20)
            
            momentum = (recent_10[-1] - recent_10[0]) / recent_10[0] * 100
            
            volatility = statistics.stdev(recent_10) if len(recent_10) > 1 else 0
            
            distance_from_ma = ((current_price - ma_20) / ma_20) * 100
            
            print(f"[DEBUG] Análise: preço={current_price:.2f}, ma20={ma_20:.2f}, momentum={momentum:.4f}%, vol={volatility:.4f}, dist={distance_from_ma:.4f}%")
            
            # CONDIÇÕES BASE - BALANCEADAS
            call_conditions = [
                current_price < ma_20,
                momentum < -0.07,
                distance_from_ma < -0.18,
                volatility > 0.18
            ]
            
            put_conditions = [
                current_price > ma_20,
                momentum > 0.07,
                distance_from_ma > 0.18,
                volatility > 0.18
            ]
            
            call_score = sum(call_conditions)
            put_score = sum(put_conditions)
            
            print(f"[DEBUG] Scores: CALL={call_score}/4, PUT={put_score}/4")
            
            # ACEITA 4/4 DIRETO (SINAL PERFEITO)
            if call_score == 4:
                confidence = 0.90
                self.last_signal_tick = self.total_ticks_received
                print(f"🎯 SINAL PERFEITO! CALL com {confidence*100:.1f}% confiança (4/4)")
                return True, "CALL", confidence
            
            if put_score == 4:
                confidence = 0.90
                self.last_signal_tick = self.total_ticks_received
                print(f"🎯 SINAL PERFEITO! PUT com {confidence*100:.1f}% confiança (4/4)")
                return True, "PUT", confidence
            
            # PARA 3/4: Filtro inteligente - pelo menos 2 das 3 métricas extras fortes
            if call_score == 3:
                strong_signals = 0
                if abs(momentum) > 0.09:
                    strong_signals += 1
                if volatility > 0.22:
                    strong_signals += 1
                if abs(distance_from_ma) > 0.22:
                    strong_signals += 1
                
                if strong_signals >= 2:
                    confidence = 0.75
                    self.last_signal_tick = self.total_ticks_received
                    print(f"🎯 SINAL BOM! CALL com {confidence*100:.1f}% confiança (3/4 com {strong_signals}/3 fortes)")
                    return True, "CALL", confidence
                else:
                    print(f"[DEBUG] CALL 3/4 mas só {strong_signals}/3 métricas fortes (precisa 2+)")
                    return False, None, 0.0
            
            if put_score == 3:
                strong_signals = 0
                if abs(momentum) > 0.09:
                    strong_signals += 1
                if volatility > 0.22:
                    strong_signals += 1
                if abs(distance_from_ma) > 0.22:
                    strong_signals += 1
                
                if strong_signals >= 2:
                    confidence = 0.75
                    self.last_signal_tick = self.total_ticks_received
                    print(f"🎯 SINAL BOM! PUT com {confidence*100:.1f}% confiança (3/4 com {strong_signals}/3 fortes)")
                    return True, "PUT", confidence
                else:
                    print(f"[DEBUG] PUT 3/4 mas só {strong_signals}/3 métricas fortes (precisa 2+)")
                    return False, None, 0.0
            
            print(f"[DEBUG] Nenhum sinal forte o suficiente")
            return False, None, 0.0
            
        except Exception as e:
            print(f"⚠️ Erro na análise: {e}")
            return False, None, 0.0
    
    def get_contract_params(self, direction):
        """Retorna parâmetros do contrato"""
        return {
            "contract_type": direction,
            "duration": 4,
            "duration_unit": "t",
            "symbol": BotConfig.DEFAULT_SYMBOL,
            "basis": BotConfig.BASIS
        }
    
    def get_info(self):
        """Informações da estratégia"""
        return {
            'name': self.name,
            'tier': 'Intermediária',
            'min_history': self.min_history,
            'cooldown': self.cooldown_ticks,
            'expected_win_rate': '55-65%',
            'trades_per_hour': '3-6',
            'indicators': 'MA10, MA20, Momentum, Volatilidade',
            'risk_level': 'Médio'
        }
