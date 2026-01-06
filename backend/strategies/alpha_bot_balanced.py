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
        self.cooldown_ticks = 15  # Aumentado: menos trades, mais qualidade
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
            
            # CONDIÇÕES MAIS RIGOROSAS - SÓ SINAIS FORTES
            call_conditions = [
                current_price < ma_20,
                momentum < -0.08,  # Momentum FORTE (era -0.06)
                distance_from_ma < -0.20,  # Distância GRANDE (era -0.18)
                volatility > 0.20  # Volatilidade ALTA (era 0.12)
            ]
            
            put_conditions = [
                current_price > ma_20,
                momentum > 0.08,  # Momentum FORTE
                distance_from_ma > 0.20,  # Distância GRANDE
                volatility > 0.20  # Volatilidade ALTA
            ]
            
            call_score = sum(call_conditions)
            put_score = sum(put_conditions)
            
            print(f"[DEBUG] Scores: CALL={call_score}/4, PUT={put_score}/4")
            
            # ACEITA 3/4 OU 4/4
            # MAS 3/4 precisa ter TODAS as condições MUITO fortes
            if call_score >= 3:
                # Se 3/4, verifica se são condições REALMENTE fortes
                if call_score == 3:
                    # Precisa de momentum E volatilidade E distância EXTRAS
                    extra_strong = (
                        abs(momentum) > 0.10 and  # Momentum EXTRA forte
                        volatility > 0.25 and  # Volatilidade EXTRA alta
                        abs(distance_from_ma) > 0.25  # Distância EXTRA grande
                    )
                    if not extra_strong:
                        print(f"[DEBUG] CALL 3/4 mas condições não são fortes o suficiente")
                        return False, None, 0.0
                
                confidence = (call_score / 4) * 0.90 + 0.10  # 70-90%
                self.last_signal_tick = self.total_ticks_received
                print(f"🎯 SINAL DETECTADO! CALL com {confidence*100:.1f}% confiança ({call_score}/4)")
                return True, "CALL", confidence
            
            if put_score >= 3:
                # Se 3/4, verifica se são condições REALMENTE fortes
                if put_score == 3:
                    extra_strong = (
                        abs(momentum) > 0.10 and
                        volatility > 0.25 and
                        abs(distance_from_ma) > 0.25
                    )
                    if not extra_strong:
                        print(f"[DEBUG] PUT 3/4 mas condições não são fortes o suficiente")
                        return False, None, 0.0
                
                confidence = (put_score / 4) * 0.90 + 0.10  # 70-90%
                self.last_signal_tick = self.total_ticks_received
                print(f"🎯 SINAL DETECTADO! PUT com {confidence*100:.1f}% confiança ({put_score}/4)")
                return True, "PUT", confidence
            
            print(f"[DEBUG] Nenhum sinal forte o suficiente")
            return False, None, 0.0
            
        except Exception as e:
            print(f"⚠️ Erro na análise: {e}")
            return False, None, 0.0
    
    def get_contract_params(self, direction):
        """Retorna parâmetros do contrato"""
        return {
            "contract_type": direction,
            "duration": 4,  # 4 ticks (8-12 segundos) - mais tempo para tendência se confirmar
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
            'trades_per_hour': '2-4',
            'indicators': 'MA10, MA20, Momentum, Volatilidade',
            'risk_level': 'Médio'
        }
