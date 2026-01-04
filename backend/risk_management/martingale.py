"""
Sistema de Martingale para gestão de progressão
Alpha Dolar 2.0
"""
try:
    from ..config import BotConfig
except ImportError:
    from config import BotConfig

class Martingale:
    """Gerencia progressão de stake com Martingale"""

    def __init__(self, stake_inicial=None, multiplicador=None, max_steps=None):
        self.stake_inicial = stake_inicial or BotConfig.STAKE_INICIAL
        self.multiplicador = multiplicador or BotConfig.MULTIPLICADOR_MARTINGALE
        self.max_steps = max_steps or BotConfig.MAX_MARTINGALE_STEPS

        # Estado atual
        self.stake_atual = self.stake_inicial
        self.step_atual = 0
        self.total_investido = 0.0
        self.ciclos_completos = 0

    def calcular_proximo_stake(self, vitoria=False):
        """
        Calcula o próximo stake baseado em vitória ou derrota

        Args:
            vitoria (bool): True se ganhou, False se perdeu

        Returns:
            float: Próximo valor de stake
        """
        if vitoria:
            # Reset ao valor inicial após vitória
            self.stake_atual = self.stake_inicial
            self.step_atual = 0
            self.ciclos_completos += 1
            return self.stake_atual
        else:
            # Aumenta stake após derrota
            if self.step_atual < self.max_steps:
                self.step_atual += 1
                self.stake_atual *= self.multiplicador
            else:
                # Reset se atingiu máximo de tentativas
                self.stake_atual = self.stake_inicial
                self.step_atual = 0

            return self.stake_atual

    def reset(self):
        """Reset completo do martingale"""
        self.stake_atual = self.stake_inicial
        self.step_atual = 0
        self.total_investido = 0.0

    def pode_continuar(self, saldo_disponivel):
        """
        Verifica se tem saldo suficiente para próximo stake

        Args:
            saldo_disponivel (float): Saldo atual da conta

        Returns:
            bool: True se pode continuar
        """
        proximo_stake = self.stake_atual * self.multiplicador
        return saldo_disponivel >= proximo_stake

    def registrar_trade(self, valor):
        """Registra valor investido em trade"""
        self.total_investido += valor

    def get_info(self):
        """Retorna informações do estado atual"""
        return {
            "stake_atual": round(self.stake_atual, 2),
            "step_atual": self.step_atual,
            "max_steps": self.max_steps,
            "total_investido": round(self.total_investido, 2),
            "ciclos_completos": self.ciclos_completos,
            "proximo_stake_derrota": round(self.stake_atual * self.multiplicador, 2)
        }

class AntiMartingale(Martingale):
    """
    Sistema Anti-Martingale (aumenta após vitória, diminui após derrota)
    Também conhecido como Paroli
    """

    def calcular_proximo_stake(self, vitoria=False):
        """
        Calcula o próximo stake - INVERSO do Martingale tradicional

        Args:
            vitoria (bool): True se ganhou, False se perdeu

        Returns:
            float: Próximo valor de stake
        """
        if vitoria:
            # Aumenta stake após vitória
            if self.step_atual < self.max_steps:
                self.step_atual += 1
                self.stake_atual *= self.multiplicador
            else:
                # Reset se atingiu máximo
                self.stake_atual = self.stake_inicial
                self.step_atual = 0
                self.ciclos_completos += 1

            return self.stake_atual
        else:
            # Reset ao valor inicial após derrota
            self.stake_atual = self.stake_inicial
            self.step_atual = 0
            return self.stake_atual

class DAlembert:
    """
    Sistema D'Alembert (progressão aritmética ao invés de geométrica)
    Mais conservador que Martingale
    """

    def __init__(self, stake_inicial=None, incremento=None, max_steps=None):
        self.stake_inicial = stake_inicial or BotConfig.STAKE_INICIAL
        self.incremento = incremento or 1.0  # Quanto adicionar/subtrair
        self.max_steps = max_steps or BotConfig.MAX_MARTINGALE_STEPS

        self.stake_atual = self.stake_inicial
        self.step_atual = 0
        self.total_investido = 0.0
        self.ciclos_completos = 0

    def calcular_proximo_stake(self, vitoria=False):
        """
        Calcula próximo stake com progressão aritmética

        Args:
            vitoria (bool): True se ganhou, False se perdeu

        Returns:
            float: Próximo valor de stake
        """
        if vitoria:
            # Diminui stake após vitória
            if self.step_atual > 0:
                self.step_atual -= 1
                self.stake_atual -= self.incremento
            else:
                # Já está no mínimo
                self.ciclos_completos += 1

            # Não deixa ficar menor que inicial
            if self.stake_atual < self.stake_inicial:
                self.stake_atual = self.stake_inicial

            return self.stake_atual
        else:
            # Aumenta stake após derrota
            if self.step_atual < self.max_steps:
                self.step_atual += 1
                self.stake_atual += self.incremento
            else:
                # Reset se atingiu máximo
                self.stake_atual = self.stake_inicial
                self.step_atual = 0

            return self.stake_atual

    def reset(self):
        """Reset completo"""
        self.stake_atual = self.stake_inicial
        self.step_atual = 0
        self.total_investido = 0.0

    def pode_continuar(self, saldo_disponivel):
        """Verifica se tem saldo para próximo stake"""
        proximo_stake = self.stake_atual + self.incremento
        return saldo_disponivel >= proximo_stake

    def registrar_trade(self, valor):
        """Registra valor investido"""
        self.total_investido += valor

    def get_info(self):
        """Informações do estado atual"""
        return {
            "stake_atual": round(self.stake_atual, 2),
            "step_atual": self.step_atual,
            "max_steps": self.max_steps,
            "total_investido": round(self.total_investido, 2),
            "ciclos_completos": self.ciclos_completos,
            "proximo_stake_derrota": round(self.stake_atual + self.incremento, 2),
            "proximo_stake_vitoria": round(max(self.stake_atual - self.incremento, self.stake_inicial), 2)
        }

class Fibonacci:
    """
    Sistema Fibonacci (progressão baseada na sequência de Fibonacci)
    1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89...
    """

    def __init__(self, stake_inicial=None, max_steps=None):
        self.stake_inicial = stake_inicial or BotConfig.STAKE_INICIAL
        self.max_steps = max_steps or 10

        # Sequência Fibonacci
        self.fibonacci = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]

        self.step_atual = 0
        self.stake_atual = self.stake_inicial
        self.total_investido = 0.0
        self.ciclos_completos = 0

    def calcular_proximo_stake(self, vitoria=False):
        """
        Calcula próximo stake baseado na sequência Fibonacci

        Args:
            vitoria (bool): True se ganhou, False se perdeu

        Returns:
            float: Próximo valor de stake
        """
        if vitoria:
            # Volta 2 passos após vitória
            if self.step_atual >= 2:
                self.step_atual -= 2
            else:
                self.step_atual = 0
                self.ciclos_completos += 1
        else:
            # Avança 1 passo após derrota
            if self.step_atual < len(self.fibonacci) - 1 and self.step_atual < self.max_steps:
                self.step_atual += 1
            else:
                # Reset se atingiu máximo
                self.step_atual = 0

        # Calcula stake baseado na posição Fibonacci
        multiplicador = self.fibonacci[self.step_atual]
        self.stake_atual = self.stake_inicial * multiplicador

        return self.stake_atual

    def reset(self):
        """Reset completo"""
        self.step_atual = 0
        self.stake_atual = self.stake_inicial
        self.total_investido = 0.0

    def pode_continuar(self, saldo_disponivel):
        """Verifica se tem saldo para próximo stake"""
        proximo_step = min(self.step_atual + 1, len(self.fibonacci) - 1)
        proximo_stake = self.stake_inicial * self.fibonacci[proximo_step]
        return saldo_disponivel >= proximo_stake

    def registrar_trade(self, valor):
        """Registra valor investido"""
        self.total_investido += valor

    def get_info(self):
        """Informações do estado atual"""
        return {
            "stake_atual": round(self.stake_atual, 2),
            "step_atual": self.step_atual,
            "fibonacci_atual": self.fibonacci[self.step_atual],
            "max_steps": self.max_steps,
            "total_investido": round(self.total_investido, 2),
            "ciclos_completos": self.ciclos_completos
        }

# ===== TESTE =====
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎰 TESTE DE SISTEMAS DE PROGRESSÃO")
    print("="*60 + "\n")

    # Teste Martingale
    print("📊 MARTINGALE CLÁSSICO:")
    print("-" * 40)
    martingale = Martingale(stake_inicial=1.0, multiplicador=2.0, max_steps=5)

    # Simula sequência: Derrota, Derrota, Derrota, Vitória
    resultados = [False, False, False, True]

    for i, resultado in enumerate(resultados):
        stake = martingale.calcular_proximo_stake(resultado)
        status = "✅ VITÓRIA" if resultado else "❌ DERROTA"
        print(f"Trade {i+1}: {status} → Próximo stake: ${stake:.2f}")
        martingale.registrar_trade(stake)

    print(f"\nInfo final: {martingale.get_info()}\n")

    # Teste Anti-Martingale
    print("\n📊 ANTI-MARTINGALE (PAROLI):")
    print("-" * 40)
    anti = AntiMartingale(stake_inicial=1.0, multiplicador=2.0, max_steps=3)

    # Simula sequência: Vitória, Vitória, Vitória, Derrota
    resultados = [True, True, True, False]

    for i, resultado in enumerate(resultados):
        stake = anti.calcular_proximo_stake(resultado)
        status = "✅ VITÓRIA" if resultado else "❌ DERROTA"
        print(f"Trade {i+1}: {status} → Próximo stake: ${stake:.2f}")
        anti.registrar_trade(stake)

    print(f"\nInfo final: {anti.get_info()}\n")

    # Teste D'Alembert
    print("\n📊 D'ALEMBERT:")
    print("-" * 40)
    dalembert = DAlembert(stake_inicial=1.0, incremento=0.5, max_steps=5)

    # Simula sequência mista
    resultados = [False, False, True, False, True, True]

    for i, resultado in enumerate(resultados):
        stake = dalembert.calcular_proximo_stake(resultado)
        status = "✅ VITÓRIA" if resultado else "❌ DERROTA"
        print(f"Trade {i+1}: {status} → Próximo stake: ${stake:.2f}")
        dalembert.registrar_trade(stake)

    print(f"\nInfo final: {dalembert.get_info()}\n")

    # Teste Fibonacci
    print("\n📊 FIBONACCI:")
    print("-" * 40)
    fib = Fibonacci(stake_inicial=1.0, max_steps=8)

    # Simula sequência
    resultados = [False, False, False, True, False, True, True]

    for i, resultado in enumerate(resultados):
        stake = fib.calcular_proximo_stake(resultado)
        status = "✅ VITÓRIA" if resultado else "❌ DERROTA"
        print(f"Trade {i+1}: {status} → Próximo stake: ${stake:.2f}")
        fib.registrar_trade(stake)

    print(f"\nInfo final: {fib.get_info()}\n")
