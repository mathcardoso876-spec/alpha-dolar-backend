"""
ALPHA DOLAR 2.0 - API Flask
Backend com suporte REAL / DEMO
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import time
import random

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 🔐 TOKENS (Render ENV)
DEMO_TOKEN = os.environ.get("DEMO_TOKEN", "demo_token_fake")
REAL_TOKEN = os.environ.get("REAL_TOKEN", "real_token_fake")

# 🤖 Estado dos bots
bot_states = {
    'ia': {
        'running': False,
        'stats': {},
        'start_time': None,
        'account_type': 'demo',
        'token': None
    }
}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "environment": "production",
        "version": "2.1.0",
        "demo_token_configured": bool(DEMO_TOKEN),
        "real_token_configured": bool(REAL_TOKEN)
    })

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    data = request.json or {}

    bot_type = data.get('bot_type')
    account_type = data.get('account_type', 'demo')
    config = data.get('config', {})

    if bot_type not in bot_states:
        return jsonify({"success": False, "error": "Bot não encontrado"}), 400

    bot = bot_states[bot_type]

    if bot['running']:
        return jsonify({"success": False, "error": "Bot já está rodando"}), 400

    # 🔐 Seleção de token
    if account_type == 'real':
        if not REAL_TOKEN:
            return jsonify({"success": False, "error": "Token REAL não configurado"}), 400
        token = REAL_TOKEN
    else:
        token = DEMO_TOKEN

    # 📦 Inicializa bot
    bot['running'] = True
    bot['start_time'] = time.time()
    bot['account_type'] = account_type
    bot['token'] = token
    bot['stats'] = {
        "balance": 10000.0 if account_type == 'demo' else 0.92,
        "saldo_liquido": 0.0,
        "wins": 0,
        "losses": 0,
        "total_trades": 0
    }

    print(f"🚀 Bot iniciado | Conta: {account_type.upper()}")

    return jsonify({
        "success": True,
        "message": "Bot iniciado",
        "account_type": account_type
    })

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    data = request.json or {}
    bot_type = data.get('bot_type')

    if bot_type not in bot_states:
        return jsonify({"success": False, "error": "Bot não encontrado"}), 400

    bot_states[bot_type]['running'] = False

    return jsonify({
        "success": True,
        "message": "Bot parado"
    })

@app.route('/api/bot/stats/<bot_type>', methods=['GET'])
def bot_stats(bot_type):
    if bot_type not in bot_states:
        return jsonify({"success": False}), 404

    bot = bot_states[bot_type]

    if not bot['running']:
        return jsonify({"running": False})

    stats = bot['stats']

    # simulação
    if random.random() > 0.5:
        profit = random.uniform(0.1, 1.5)
        stats['wins'] += 1
    else:
        profit = -random.uniform(0.1, 1.0)
        stats['losses'] += 1

    stats['saldo_liquido'] += profit
    stats['balance'] += profit
    stats['total_trades'] += 1

    return jsonify({
        "running": True,
        "account_type": bot['account_type'],
        "stats": stats
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("🔥 Alpha Dolar Backend rodando")
    app.run(host="0.0.0.0", port=port)
