# 🚀 INSTRUÇÕES DE DEPLOY - ALPHA DOLAR 2.0

## ⚠️ IMPORTANTE: ARQUIVOS FALTANDO

Este pacote contém a estrutura básica. Você precisa adicionar manualmente:

### 📁 Arquivos do Backend (copiar do PythonAnywhere):

```
backend/
├── __init__.py
├── bot.py                    # Arquivo principal do bot
├── deriv_api.py             # Conexão com Deriv (COM AUTO-COMPRA)
├── stop_loss.py             # Gerenciamento de risco
└── strategies/
    ├── __init__.py
    ├── base_strategy.py
    ├── alpha_bot_1.py
    ├── alpha_bot_balanced.py    # ← IMPORTANTE!
    └── test_strategy.py
```

## 📥 COMO PEGAR OS ARQUIVOS:

### No PythonAnywhere:

```bash
cd ~/alpha-dolar-2.0/backend
cat bot.py
cat deriv_api.py
cat stop_loss.py
cat strategies/base_strategy.py
cat strategies/alpha_bot_1.py
cat strategies/alpha_bot_balanced.py
cat strategies/test_strategy.py
```

Copie cada arquivo e crie no projeto.

## 🔑 PASSO 1: Criar Repositório GitHub

1. Vá em https://github.com/new
2. Nome: `alpha-dolar-backend`
3. Público
4. Não adicione README (já temos)
5. Clique "Create repository"

## 📤 PASSO 2: Upload dos Arquivos

### Opção A - Via GitHub Web:

1. No repositório criado, clique "uploading an existing file"
2. Arraste TODOS os arquivos desta pasta
3. Commit

### Opção B - Via Git (se tiver instalado):

```bash
git init
git add .
git commit -m "Initial commit - Alpha Dolar Backend"
git branch -M main
git remote add origin https://github.com/SEU_USER/alpha-dolar-backend.git
git push -u origin main
```

## 🎯 PASSO 3: Deploy no Render

1. No Render, cole a URL do repositório:
   ```
   https://github.com/SEU_USER/alpha-dolar-backend
   ```

2. Configurações:
   - **Name**: `alpha-dolar-bot`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: (deixe vazio, usa Procfile)

3. **Environment Variables** (IMPORTANTE!):
   ```
   DERIV_TOKEN = FiOl9bCKDJWpZaj
   FLASK_ENV = production
   DEBUG = False
   ```

4. **Clique "Create Web Service"**

## ⏱️ AGUARDE:

- Deploy leva ~5 minutos
- Você verá logs em tempo real
- Quando aparecer "Live", está pronto!

## ✅ TESTAR:

Acesse: `https://seu-app.onrender.com/api/health`

Deve retornar:
```json
{
  "status": "ok",
  "message": "Alpha Dolar API Running on Render",
  "bots_available": true,
  "token_configured": true
}
```

## 🔗 ATUALIZAR FRONTEND:

No arquivo `trading.html` (PythonAnywhere), mude:

```javascript
// ANTES:
const API_URL = window.location.origin + '/api';

// DEPOIS:
const API_URL = 'https://seu-app.onrender.com/api';
```

## 🎉 PRONTO!

Bot rodando no Render + Frontend no PythonAnywhere = Sistema completo!

---

## ❓ PROBLEMAS?

- **Token inválido**: Verifique variável DERIV_TOKEN
- **Import error**: Faltam arquivos do backend
- **500 error**: Veja logs no Render Dashboard

