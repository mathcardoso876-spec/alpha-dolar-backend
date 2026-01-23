"""
ALPHA DOLAR 2.0 - API Flask (REGISTROS + INTEGRAÇÃO FRONTEND)
Backend para Alpha Dolar 2.0
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import random
import time
from datetime import datetime
from collections import deque

# ===============================
# 🚀 APP
# ===============================

app = Flask(__name__)

# ===============================
# 🌍 CORS LIBERADO (GLOBAL)
# ===============================

CORS(app)

# ===============================
# ❤️ ROTA RAIZ (EVITA ERRO 404 NO RENDER)
# ===============================

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Alpha Dolar Backend Rodando 🚀",
        "routes": [
            "/api/health",
            "/api/bot/start",
            "/api/bot/stop",
            "/api/bot/stats/<bot_type>",
            "/api/bot/trades/<bot_type>",
            "/api/account/balance",
            "/teste123"
        ]
    })

# ===============================
# 🧪 ROTA TESTE
# ===============================

@app.route('/teste123')
def teste123():
    return "ROTA TESTE OK ✅", 200

# ===============================
# 🔥 ESTADO GLOBAL DOS BOTS
# ===============================

MAX_TRADES_HISTORY = 100

def create_bot_state():
    return {
        'running': False,
        'stats': {},
        'start_time': None,
        'trades': deque(maxlen=MAX_TRADES_HISTORY)
    }

bot_states = {
    'manual': create_bot_state(),
    'ia-simples': create_bot_state(),
    'ia-avancado': create_bot_state(),
    'ia': create_bot_state()
}

# ===============================
# 💰 GET ACCOUNT BALANCE
# ===============================

@app.route('/api/account/balance', methods=['GET'])
def get_balance():
    acc_type = request.args.get('type', 'demo')

    if acc_type == 'real':
        balance = 100.00
    else:
        balance = 50.00

    return jsonify({
        "balance": balance,
        "type": acc_type
    })

# ===============================
# 🚀 START BOT
# ===============================

@app.route('/api/bot/start', methods=['POST', 'OPTIONS'])
def start_bot():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    data = request.json or {}
    bot_type = data.get('bot_type')

    if bot_type not in bot_states:
        return jsonify({'success': False, 'error': 'Bot não encontrado'}), 400

    if bot_states[bot_type]['running']:
        return jsonify({'success': False, 'error': 'Bot já está rodando'}), 400

    bot_states[bot_type]['running'] = True
    bot_states[bot_type]['start_time'] = time.time()
    bot_states[bot_type]['trades'].clear()

    bot_states[bot_type]['stats'] = {
        'balance': 10000.00,
        'saldo_liquido': 0.00,
        'win_rate': 0.0,
        'total_trades': 0,
        'wins': 0,
        'losses': 0
    }

    return jsonify({
        'success': True,
        'message': f'Bot {bot_type} iniciado!',
        'bot_type': bot_type,
        'mode': 'demo'
    })

# ===============================
# 🛑 STOP BOT
# ===============================

@app.route('/api/bot/stop', methods=['POST', 'OPTIONS'])
def stop_bot():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    data = request.json or {}
    bot_type = data.get('bot_type')

    if bot_type not in bot_states:
        return jsonify({'success': False, 'error': 'Bot não encontrado'}), 400

    bot_states[bot_type]['running'] = False

    return jsonify({
        'success': True,
        'message': f'Bot {bot_type} parado!'
    })

# ===============================
# 📊 BOT STATS + SIMULA TRADES
# ===============================

@app.route('/api/bot/stats/<bot_type>', methods=['GET', 'OPTIONS'])
def bot_stats(bot_type):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    if bot_type not in bot_states:
        return jsonify({'success': False, 'error': 'Bot não encontrado'}), 404
    
    bot = bot_states[bot_type]

    if not bot['running']:
        return jsonify({
            'success': True,
            'bot_running': False,
            'stats': bot.get('stats', {})
        })

    stats = bot['stats']
    elapsed = time.time() - bot['start_time']

    # ⏱️ Simula um trade a cada 6 segundos
    if elapsed > 6:
        gerar_trade(bot)
        bot['start_time'] = time.time()

    return jsonify({
        'success': True,
        'bot_running': True,
        'stats': stats
    })

# ===============================
# 🧾 REGISTROS DE TRADES
# ===============================

@app.route('/api/bot/trades/<bot_type>', methods=['GET'])
def get_trades(bot_type):
    if bot_type not in bot_states:
        return jsonify({'success': False, 'error': 'Bot não encontrado'}), 404

    trades = list(bot_states[bot_type]['trades'])
    return jsonify({
        'success': True,
        'total': len(trades),
        'trades': trades
    })

# ===============================
# ❤️ HEALTH CHECK
# ===============================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Alpha Dolar API Running on Render'
    })

# ===============================
# ⚙️ FUNÇÃO DE SIMULAÇÃO
# ===============================

def gerar_trade(bot):
    stats = bot['stats']

    is_win = random.random() > 0.4
    profit = round(random.uniform(1.0, 3.0), 2) if is_win else round(random.uniform(-1.0, -2.5), 2)

    stats['total_trades'] += 1

    if is_win:
        stats['wins'] += 1
        resultado = "WIN"
    else:
        stats['losses'] += 1
        resultado = "LOSS"

    stats['saldo_liquido'] += profit
    stats['balance'] = round(10000 + stats['saldo_liquido'], 2)
    stats['win_rate'] = round((stats['wins'] / stats['total_trades']) * 100, 2)

    trade = {
        'id': stats['total_trades'],
        'resultado': resultado,
        'profit': profit,
        'balance': stats['balance'],
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    bot['trades'].appendleft(trade)

# ===============================
# 🚀 START SERVER
# ===============================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 Alpha Dolar 2.0 API")
    print(f"🌐 Porta: {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
