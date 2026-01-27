"""
ALPHA DOLAR 2.0 - API Flask (ESTADO CORRETO + FRONTEND OK)
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
CORS(app)

# ===============================
# 🔥 CONFIG
# ===============================

MAX_TRADES_HISTORY = 100

# ===============================
# 🧠 ESTADO DO BOT
# ===============================

def create_bot_state():
    return {
        'running': False,
        'stats': {},
        'start_time': None,        # quando o bot iniciou
        'last_trade_time': None,   # controle de intervalo de trades
        'trades': deque(maxlen=MAX_TRADES_HISTORY)
    }

bot_states = {
    'manual': create_bot_state(),
    'ia-simples': create_bot_state(),
    'ia-avancado': create_bot_state(),
    'ia': create_bot_state()
}

# ===============================
# ❤️ ROTA RAIZ
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
            "/api/account/balance"
        ]
    })

# ===============================
# 💰 ACCOUNT BALANCE
# ===============================

@app.route('/api/account/balance', methods=['GET'])
def get_balance():
    acc_type = request.args.get('type', 'demo')
    balance = 100.00 if acc_type == 'real' else 50.00

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

    bot = bot_states[bot_type]

    if bot['running']:
        return jsonify({'success': False, 'error': 'Bot já está rodando'}), 400

    now = time.time()

    bot['running'] = True
    bot['start_time'] = now
    bot['last_trade_time'] = now
    bot['trades'].clear()

    bot['stats'] = {
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
# 📊 BOT STATS
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

    elapsed = time.time() - bot['last_trade_time']

    # ⏱️ gera trade a cada 6s
    if elapsed > 6:
        gerar_trade(bot)
        bot['last_trade_time'] = time.time()

    return jsonify({
        'success': True,
        'bot_running': True,
        'stats': bot['stats']
    })

# ===============================
# 🧾 TRADES
# ===============================

@app.route('/api/bot/trades/<bot_type>', methods=['GET'])
def get_trades(bot_type):
    if bot_type not in bot_states:
        return jsonify({'success': False, 'error': 'Bot não encontrado'}), 404

    return jsonify({
        'success': True,
        'total': len(bot_states[bot_type]['trades']),
        'trades': list(bot_states[bot_type]['trades'])
    })

# ===============================
# ❤️ HEALTH
# ===============================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Alpha Dolar API Running on Render'
    })

# ===============================
# ⚙️ SIMULA TRADE
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
