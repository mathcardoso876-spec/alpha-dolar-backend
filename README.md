# Alpha Dolar 2.0 - Backend API

Bot de trading automatizado para Deriv usando estratégias de IA.

## 🚀 Deploy no Render.com

### Passo 1: Configurar Variáveis de Ambiente

No Render Dashboard, adicione:
- `DERIV_TOKEN`: Seu token da Deriv API

### Passo 2: Deploy

1. Conecte este repositório no Render
2. Selecione "Web Service"
3. Build Command: `pip install -r requirements.txt`
4. Start Command: (automático via Procfile)
5. Clique em "Create Web Service"

## 📋 Estrutura

```
backend/
├── bot.py                    # Bot principal
├── deriv_api.py             # Conexão Deriv
├── config.py                # Configurações
├── stop_loss.py             # Gerenciamento de risco
└── strategies/              # Estratégias de trading
    ├── base_strategy.py
    ├── alpha_bot_1.py
    ├── alpha_bot_balanced.py
    └── test_strategy.py
```

## 🔧 Desenvolvimento Local

```bash
pip install -r requirements.txt
cp .env.example .env
# Edite .env com seu token
python alpha_bot_api_production.py
```

## 📊 Endpoints da API

- `GET /api/health` - Status da API
- `POST /api/bot/start` - Iniciar bot
- `POST /api/bot/stop` - Parar bot
- `GET /api/bot/stats/:type` - Estatísticas
- `GET /api/balance` - Saldo Deriv

## 🎯 Estratégias Disponíveis

1. **AlphaBot1**: Conservadora, Win Rate ~65%
2. **AlphaBotBalanced**: Intermediária, Win Rate ~55-60%
3. **TestStrategy**: Teste rápido, Win Rate ~33%

## 🔐 Segurança

- Token armazenado em variável de ambiente
- CORS configurado
- Rate limiting implementado

## 📝 Licença

Proprietary - Alpha Dolar 2.0
