"""
ALPHA DOLAR 2.0 - API Flask (VERSÃO FAKE PARA TESTES)
Retorna dados simulados para testar interface SEM bot Python rodando
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sys
import os
import random
import time
from datetime import datetime

# Adiciona path do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

app = Flask(__name__)
CORS(app)

# Estado global dos bots
bot_states = {
    'manual': {'running': False, 'pid': None, 'stats': {}, 'start_time': None},
    'ia-simples': {'running': False, 'pid': None, 'stats': {}, 'start_time': None},
    'ia-avancado': {'running': False, 'pid': None, 'stats': {}, 'start_time': None},
    'ia': {'running': False, 'pid': None, 'stats': {}, 'start_time': None}
}

# ===== CONFIGURE SEU LINK DE AFILIADO AQUI =====
DERIV_AFFILIATE_LINK = "https://deriv.com"

# =====================================================
# ROTAS DE PÁGINA
# =====================================================

@app.route('/')
def home():
    web_path = os.path.join(os.path.dirname(__file__), 'web')
    return send_from_directory(web_path, 'login.html')

@app.route('/<path:filename>')
def serve_file(filename):
    web_path = os.path.join(os.path.dirname(__file__), 'web')
    return send_from_directory(web_path, filename)

# =====================================================
# ROTAS DE API - BOTS
# =====================================================

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    data = request.json
    bot_type = data.get('bot_type')

    if bot_type not in bot_states:
        return jsonify({'error': f'Bot {bot_type} não encontrado'}), 400

    if bot_states[bot_type]['running']:
        return jsonify({'error': f'Bot {bot_type} já está rodando'}), 400

    # MARCA COMO RODANDO
    bot_states[bot_type]['running'] = True
    bot_states[bot_type]['start_time'] = time.time()
    
    # INICIALIZA STATS FAKE
    bot_states[bot_type]['stats'] = {
        'saldo_atual': 1000.00,
        'saldo_inicial': 1000.00,
        'lucro_liquido': 0.00,
        'win_rate': 0.0,
        'total_trades': 0,
        'wins': 0,
        'losses': 0,
        'trades': []
    }

    print(f"✅ Bot {bot_type} iniciado (MODO FAKE)")

    return jsonify({
        'success': True,
        'message': f'Bot {bot_type} iniciado com sucesso!',
        'bot_type': bot_type,
        'mode': 'FAKE - DADOS SIMULADOS'
    })

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    data = request.json
    bot_type = data.get('bot_type')

    if bot_type not in bot_states:
        return jsonify({'error': f'Bot {bot_type} não encontrado'}), 400

    # MARCA COMO PARADO
    bot_states[bot_type]['running'] = False
    bot_states[bot_type]['start_time'] = None

    print(f"🛑 Bot {bot_type} parado")

    return jsonify({
        'success': True,
        'message': f'Bot {bot_type} parado!'
    })

# =====================================================
# ROTA CRÍTICA: STATS DO BOT (COM DADOS FAKE)
# =====================================================

@app.route('/api/bot/stats/<bot_type>')
def bot_stats(bot_type):
    """
    Retorna estatísticas FAKE do bot
    Simula um bot operando com dados aleatórios
    """
    if bot_type not in bot_states:
        return jsonify({'error': f'Bot {bot_type} não encontrado'}), 404
    
    bot = bot_states[bot_type]
    
    # Se bot não está rodando
    if not bot['running']:
        return jsonify({
            'success': True,
            'bot_running': False,
            'saldo_atual': 0.00,
            'lucro_liquido': 0.00,
            'win_rate': 0.0,
            'total_trades': 0,
            'trades': []
        })
    
    # Bot está rodando - SIMULA DADOS
    stats = bot.get('stats', {})
    
    # Calcula tempo rodando
    elapsed = time.time() - bot['start_time']
    
    # Simula trades a cada 30 segundos
    if elapsed > 30 and stats['total_trades'] < 20:
        # Adiciona um trade fake
        is_win = random.random() > 0.35  # 65% win rate
        profit = random.uniform(1.5, 3.0) if is_win else random.uniform(-1.0, -2.0)
        
        stats['total_trades'] += 1
        if is_win:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
        
        stats['lucro_liquido'] += profit
        stats['saldo_atual'] = stats['saldo_inicial'] + stats['lucro_liquido']
        stats['win_rate'] = (stats['wins'] / stats['total_trades']) * 100 if stats['total_trades'] > 0 else 0
        
        # Adiciona trade ao histórico
        trade = {
            'id': stats['total_trades'],
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'CALL' if is_win else 'PUT',
            'result': 'WIN' if is_win else 'LOSS',
            'profit': profit,
            'stake': 1.0
        }
        stats['trades'].insert(0, trade)
        
        # Mantém só últimos 10 trades
        if len(stats['trades']) > 10:
            stats['trades'] = stats['trades'][:10]
        
        # Reseta timer
        bot['start_time'] = time.time()
    
    return jsonify({
        'success': True,
        'bot_running': True,
        'saldo_atual': round(stats.get('saldo_atual', 1000.00), 2),
        'lucro_liquido': round(stats.get('lucro_liquido', 0.00), 2),
        'win_rate': round(stats.get('win_rate', 0.0), 1),
        'total_trades': stats.get('total_trades', 0),
        'wins': stats.get('wins', 0),
        'losses': stats.get('losses', 0),
        'trades': stats.get('trades', [])
    })

@app.route('/api/bots/status')
def all_bots_status():
    return jsonify(bot_states)

@app.route('/api/bot/reset/<bot_type>', methods=['POST'])
def reset_bot(bot_type):
    if bot_type not in bot_states:
        return jsonify({'error': f'Bot {bot_type} não encontrado'}), 404
    
    bot_states[bot_type] = {
        'running': False,
        'pid': None,
        'stats': {},
        'start_time': None
    }
    
    return jsonify({
        'success': True,
        'message': f'Bot {bot_type} resetado!'
    })

# =====================================================
# OUTRAS ROTAS
# =====================================================

@app.route('/api/affiliate/link')
def get_affiliate_link():
    return jsonify({
        'link': DERIV_AFFILIATE_LINK,
        'platform': 'Deriv',
        'commission': '25-40%'
    })

@app.route('/api/stats/dashboard')
def dashboard_stats():
    return jsonify({
        'traders_ativos': 614,
        'robos_ativos': 27,
        'saldo_total': 10000.00,
        'trades_hoje': 0,
        'win_rate': 0,
        'lucro_perda': 0,
        'top_traders': [
            {'nome': 'Juliana Lima', 'profit': '+60%', 'avatar': 'JL'},
            {'nome': 'Thiago Mendes', 'profit': '+59%', 'avatar': 'TM'},
            {'nome': 'Alexandre Souza', 'profit': '+56%', 'avatar': 'AS'}
        ]
    })

@app.route('/api/support/links')
def support_links():
    return jsonify({
        'whatsapp': 'https://wa.me/5547999999999',
        'telegram': 'https://t.me/alphadolar',
        'instagram': 'https://instagram.com/alphadolar',
        'youtube': 'https://youtube.com/@alphadolar'
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'online',
        'version': '2.0.2-FAKE',
        'mode': 'FAKE DATA - SIMULADO',
        'bots_available': ['manual', 'ia-simples', 'ia-avancado', 'ia']
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Rota não encontrada'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Erro interno do servidor'}), 500

# =====================================================
# RUN
# =====================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 70)
    print("🚀 ALPHA DOLAR 2.0 - API FLASK (MODO FAKE)")
    print("=" * 70)
    print("⚠️  ATENÇÃO: Esta versão retorna DADOS FAKE para testes!")
    print("📊 Bots disponíveis:", list(bot_states.keys()))
    print(f"🌐 Servidor iniciando na porta {port}")
    print("=" * 70)
    app.run(debug=False, host='0.0.0.0', port=port)
