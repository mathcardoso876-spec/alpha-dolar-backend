# ALPHA DOLAR 2.0 - API PRODUCTION (RENDER.COM) - DEMO/REAL VERSION
"""
ALPHA DOLAR 2.0 - API PRODUCTION INTEGRADA
API Flask que conecta frontend web com bots Python reais
VERSÃO COM SISTEMA DEMO/REAL: Permite alternar entre contas
VERSÃO CORRIGIDA: Resposta rápida + inicialização em background + FIX estado inconsistente
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
from datetime import datetime
import sys

# Configurar paths
project_path = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(project_path, 'backend')
sys.path.insert(0, project_path)
sys.path.insert(0, backend_path)

app = Flask(__name__)

# CORS - Liberar TODAS as origens
CORS(app)

# ==================== IMPORTAR CONFIG PRIMEIRO ====================

try:
    from config import BotConfig
    CONFIG_LOADED = True
    print("✅ Config carregado com sucesso!")
except ImportError:
    try:
        from backend.config import BotConfig
        CONFIG_LOADED = True
        print("✅ Config carregado de backend/ com sucesso!")
    except ImportError as e:
        CONFIG_LOADED = False
        print(f"⚠️ Erro ao carregar config: {e}")

# ==================== IMPORTAR BOTS REAIS ====================

try:
    from backend.bot import AlphaDolar
    from backend.strategies.alpha_bot_1 import AlphaBot1
    from backend.strategies.alpha_bot_balanced import AlphaBotBalanced
    from backend.strategies.test_strategy import TestStrategy
    BOTS_AVAILABLE = True
    print("✅ Bots Python carregados com sucesso!")
except ImportError as e:
    BOTS_AVAILABLE = False
    print(f"⚠️ Erro ao importar bots: {e}")
    print("   Sistema funcionará em modo simulado apenas")

# ==================== CONFIGURAÇÃO DEMO/REAL ====================

# Tokens DEMO e REAL
DERIV_TOKEN_DEMO = os.getenv('DERIV_TOKEN_DEMO', '')
DERIV_TOKEN_REAL = os.getenv('DERIV_TOKEN_REAL', '')

# Estado global do modo (demo ou real)
current_account_mode = 'demo'  # Inicia em DEMO por segurança
current_token = DERIV_TOKEN_DEMO

print("\n" + "="*70)
print("🔑 CONFIGURAÇÃO DE TOKENS:")
print(f"   Token DEMO: {'✅ Configurado' if DERIV_TOKEN_DEMO else '❌ NÃO configurado'}")
print(f"   Token REAL: {'✅ Configurado' if DERIV_TOKEN_REAL else '❌ NÃO configurado'}")
print(f"   Modo inicial: {current_account_mode.upper()}")
print("="*70 + "\n")

if CONFIG_LOADED and BOTS_AVAILABLE:
    BotConfig.API_TOKEN = current_token

# ==================== ESTADO GLOBAL ====================

bots_state = {
    'manual': {'running': False, 'instance': None, 'thread': None, 'status': 'stopped'},
    'ia': {'running': False, 'instance': None, 'thread': None, 'status': 'stopped'},
    'ia_simples': {'running': False, 'instance': None, 'thread': None, 'status': 'stopped'},
    'ia_avancado': {'running': False, 'instance': None, 'thread': None, 'status': 'stopped'}
}

# ==================== ROTAS API - DEMO/REAL ====================

@app.route('/api/account/mode', methods=['GET', 'POST'])
def account_mode():
    """
    GET: Retorna modo atual (demo/real)
    POST: Muda modo (demo/real)
    """
    global current_account_mode, current_token
    
    if request.method == 'GET':
        # Retorna modo atual
        return jsonify({
            'success': True,
            'mode': current_account_mode,
            'demo_available': bool(DERIV_TOKEN_DEMO),
            'real_available': bool(DERIV_TOKEN_REAL)
        })
    
    # POST - Mudar modo
    data = request.get_json()
    new_mode = data.get('mode', 'demo')
    
    if new_mode not in ['demo', 'real']:
        return jsonify({
            'success': False,
            'error': 'Modo inválido. Use "demo" ou "real"'
        }), 400
    
    # Verifica se token existe
    if new_mode == 'demo' and not DERIV_TOKEN_DEMO:
        return jsonify({
            'success': False,
            'error': 'Token DEMO não configurado. Configure DERIV_TOKEN_DEMO no Render.'
        }), 400
    
    if new_mode == 'real' and not DERIV_TOKEN_REAL:
        return jsonify({
            'success': False,
            'error': 'Token REAL não configurado. Configure DERIV_TOKEN_REAL no Render.'
        }), 400
    
    # Para todos os bots rodando antes de mudar
    stopped_bots = []
    for bot_type, state in bots_state.items():
        if state.get('running', False):
            bot = state.get('instance')
            if bot and hasattr(bot, 'stop'):
                try:
                    bot.stop()
                    stopped_bots.append(bot_type)
                except:
                    pass
            state['running'] = False
    
    # Muda modo e token
    current_account_mode = new_mode
    current_token = DERIV_TOKEN_DEMO if new_mode == 'demo' else DERIV_TOKEN_REAL
    
    # Atualiza BotConfig
    if CONFIG_LOADED and BOTS_AVAILABLE:
        BotConfig.API_TOKEN = current_token
    
    print(f"\n{'='*70}")
    print(f"🔄 MODO ALTERADO: {new_mode.upper()}")
    if stopped_bots:
        print(f"🛑 Bots parados: {', '.join(stopped_bots)}")
    print(f"{'='*70}\n")
    
    return jsonify({
        'success': True,
        'mode': current_account_mode,
        'message': f'Modo alterado para {new_mode.upper()}',
        'stopped_bots': stopped_bots
    })

@app.route('/api/account/balance')
def get_account_balance():
    """
    Retorna saldo da conta atual (DEMO ou REAL)
    """
    # Tenta pegar de algum bot rodando
    for bot_type, state in bots_state.items():
        bot = state.get('instance')
        if bot and BOTS_AVAILABLE and hasattr(bot, 'api'):
            try:
                balance = bot.api.balance
                currency = bot.api.currency
                return jsonify({
                    'success': True,
                    'balance': balance,
                    'currency': currency,
                    'mode': current_account_mode,
                    'formatted': f"${balance:,.2f}"
                })
            except:
                pass
    
    # Se nenhum bot rodando, tenta conectar direto
    if BOTS_AVAILABLE:
        try:
            from deriv_api import DerivAPI
            api = DerivAPI()
            
            # Temporariamente muda token
            old_token = BotConfig.API_TOKEN if CONFIG_LOADED else None
            if CONFIG_LOADED:
                BotConfig.API_TOKEN = current_token
            
            if api.connect() and api.authorize():
                balance = api.balance
                currency = api.currency
                api.disconnect()
                
                # Restaura token
                if old_token and CONFIG_LOADED:
                    BotConfig.API_TOKEN = old_token
                
                return jsonify({
                    'success': True,
                    'balance': balance,
                    'currency': currency,
                    'mode': current_account_mode,
                    'formatted': f"${balance:,.2f}"
                })
        except Exception as e:
            print(f"❌ Erro ao buscar saldo direto: {e}")
    
    # Fallback
    fallback_balance = 0.00 if current_account_mode == 'real' else 10000.00
    return jsonify({
        'success': True,
        'balance': fallback_balance,
        'currency': 'USD',
        'mode': current_account_mode,
        'formatted': f"${fallback_balance:,.2f}",
        'note': 'Saldo de fallback - bot não conectado'
    })

# ==================== ROTAS API PADRÃO ====================

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Alpha Dolar API Running on Render',
        'version': '2.0.7-FIXED',
        'bots_available': BOTS_AVAILABLE,
        'config_loaded': CONFIG_LOADED,
        'demo_token_configured': bool(DERIV_TOKEN_DEMO),
        'real_token_configured': bool(DERIV_TOKEN_REAL),
        'current_mode': current_account_mode,
        'environment': os.getenv('FLASK_ENV', 'production')
    })

@app.route('/api/bots/status')
def get_bots_status():
    status = {}
    for bot_type, state in bots_state.items():
        bot_instance = state.get('instance')
        status[bot_type] = {
            'running': state['running'],
            'status': state.get('status', 'stopped'),
            'stats': {}
        }

        if BOTS_AVAILABLE and bot_instance and hasattr(bot_instance, 'stop_loss'):
            try:
                stats = bot_instance.stop_loss.get_estatisticas()
                status[bot_type]['stats'] = stats
            except:
                pass

    return jsonify(status)

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """
    🔥 VERSÃO CORRIGIDA: Responde IMEDIATAMENTE e inicia bot em background
    🔥 FIX: Reseta estado inconsistente antes de verificar se está rodando
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400

        # Verifica se token do modo atual existe
        if not current_token:
            return jsonify({
                'success': False,
                'error': f'Token {current_account_mode.upper()} não configurado. Configure DERIV_TOKEN_{current_account_mode.upper()} no Render.'
            }), 500

        if not CONFIG_LOADED:
            return jsonify({
                'success': False,
                'error': 'Configuração não carregada. Verifique o arquivo config.py'
            }), 500

        bot_type = data.get('bot_type', 'manual')
        config = data.get('config', {})

        print(f"\n{'='*60}")
        print(f"📥 Requisição para iniciar bot: {bot_type}")
        print(f"🔑 Modo: {current_account_mode.upper()}")
        print(f"⚙️  Config: {config}")
        print(f"{'='*60}\n")

        if bot_type not in bots_state:
            bots_state[bot_type] = {
                'running': False, 
                'instance': None, 
                'thread': None,
                'status': 'stopped'
            }

        # 🔥 FIX: RESETA ESTADO INCONSISTENTE
        # Se bot está marcado como running mas não tem instância válida, reseta
        if bots_state[bot_type].get('running', False):
            bot_instance = bots_state[bot_type].get('instance')
            
            # Verifica se a instância realmente está rodando
            is_really_running = False
            if bot_instance:
                if hasattr(bot_instance, 'running'):
                    is_really_running = bot_instance.running
                elif hasattr(bot_instance, 'api') and hasattr(bot_instance.api, 'ws'):
                    is_really_running = bot_instance.api.ws is not None
            
            # Se estado está inconsistente (marcado como running mas não rodando de verdade)
            if not is_really_running:
                print(f"⚠️ Estado inconsistente detectado - resetando bot {bot_type}")
                bots_state[bot_type]['running'] = False
                bots_state[bot_type]['status'] = 'stopped'
                bots_state[bot_type]['instance'] = None
                bots_state[bot_type]['thread'] = None

        # Agora verifica se está rodando
        if bots_state[bot_type].get('running', False):
            return jsonify({
                'success': False,
                'error': f'Bot {bot_type} já está rodando'
            }), 400

        # 🔥 MARCA COMO "INICIANDO" IMEDIATAMENTE
        bots_state[bot_type]['status'] = 'starting'
        bots_state[bot_type]['running'] = True

        if BOTS_AVAILABLE and bot_type in ['ia', 'ia_simples']:
            # Aplicar configurações
            BotConfig.DEFAULT_SYMBOL = config.get('symbol', 'R_100')
            BotConfig.STAKE_INICIAL = config.get('stake_inicial', 0.35)
            BotConfig.LUCRO_ALVO = config.get('lucro_alvo', 2.0)
            BotConfig.LIMITE_PERDA = config.get('limite_perda', 5.0)
            BotConfig.API_TOKEN = current_token

            # 🚀 FUNÇÃO QUE RODA EM BACKGROUND
            def iniciar_bot_background():
                try:
                    print(f"🔄 [BACKGROUND] Iniciando bot {bot_type}...")
                    
                    # Carrega estratégia
                    print("⚡ Carregando AlphaBotBalanced...")
                    strategy = AlphaBotBalanced()
                    print(f"✅ Estratégia carregada: {strategy.name}")
                    
                    # Cria bot
                    use_martingale = config.get('martingale', False)
                    bot = AlphaDolar(
                        strategy=strategy,
                        use_martingale=use_martingale
                    )
                    print(f"✅ Bot criado: {bot.bot_name}")
                    
                    # Salva instância
                    bots_state[bot_type]['instance'] = bot
                    bots_state[bot_type]['status'] = 'running'
                    
                    # Inicia bot
                    print(f"🚀 Iniciando loop do bot...")
                    bot.start()
                    
                except Exception as e:
                    print(f"❌ Erro ao iniciar bot em background: {e}")
                    import traceback
                    traceback.print_exc()
                    bots_state[bot_type]['running'] = False
                    bots_state[bot_type]['status'] = 'error'

            # Inicia thread em background
            thread = threading.Thread(target=iniciar_bot_background, daemon=True)
            thread.start()
            
            bots_state[bot_type]['thread'] = thread

            # 🎯 RESPONDE IMEDIATAMENTE (não espera o bot conectar)
            print(f"✅ Resposta enviada - bot iniciando em background")

            return jsonify({
                'success': True,
                'message': f'Bot {bot_type} iniciando em modo {current_account_mode.upper()}...',
                'bot_type': bot_type,
                'mode': current_account_mode,
                'status': 'starting',
                'config': {
                    'symbol': BotConfig.DEFAULT_SYMBOL,
                    'stake_inicial': BotConfig.STAKE_INICIAL,
                    'lucro_alvo': BotConfig.LUCRO_ALVO,
                    'limite_perda': BotConfig.LIMITE_PERDA,
                    'strategy': 'AlphaBotBalanced'
                }
            })

        return jsonify({
            'success': False,
            'error': 'Tipo de bot não suportado'
        }), 400

    except Exception as e:
        print(f"❌ ERRO em start_bot: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Parar bot"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400

        bot_type = data.get('bot_type', 'ia')

        print(f"🛑 Parando bot: {bot_type}")

        if bot_type not in bots_state:
            return jsonify({
                'success': False,
                'error': f'Bot {bot_type} não encontrado'
            }), 400

        bot = bots_state[bot_type].get('instance')

        if bot:
            if hasattr(bot, 'stop'):
                try:
                    bot.stop()
                except:
                    pass
            elif hasattr(bot, 'running'):
                bot.running = False

        # SEMPRE marca como parado
        bots_state[bot_type]['running'] = False
        bots_state[bot_type]['status'] = 'stopped'
        bots_state[bot_type]['instance'] = None
        bots_state[bot_type]['thread'] = None

        stats = {}
        if bot and BOTS_AVAILABLE and hasattr(bot, 'stop_loss'):
            try:
                stats = bot.stop_loss.get_estatisticas()
            except:
                pass

        print(f"✅ Bot {bot_type} parado")

        return jsonify({
            'success': True,
            'message': f'Bot {bot_type} parado com sucesso!',
            'stats': stats
        })

    except Exception as e:
        print(f"❌ ERRO em stop_bot: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/balance')
def get_balance():
    """Retorna saldo atual da conta - REDIRECIONA PARA /api/account/balance"""
    return get_account_balance()

@app.route('/api/bot/stats/<bot_type>')
def get_bot_stats(bot_type):
    """
    🔥 VERSÃO MELHORADA: Retorna status de inicialização também
    """
    if bot_type not in bots_state:
        return jsonify({'success': False, 'error': 'Bot não encontrado'}), 404

    state = bots_state[bot_type]
    bot = state.get('instance')
    status = state.get('status', 'stopped')

    # Se bot não está rodando
    if not state.get('running', False):
        return jsonify({
            'success': True,
            'bot_running': False,
            'status': 'stopped',
            'balance': 0.00,
            'saldo_liquido': 0.00,
            'win_rate': 0.0,
            'total_trades': 0,
            'trades': []
        })

    # Se bot está iniciando mas ainda não tem instância
    if status == 'starting' and not bot:
        # Busca saldo real da conta
        saldo_real = 10000.00 if current_account_mode == 'demo' else 0.00
        
        # Tenta buscar saldo real mesmo sem bot rodando
        if BOTS_AVAILABLE:
            try:
                from deriv_api import DerivAPI
                temp_api = DerivAPI()
                if temp_api.connect() and temp_api.authorize():
                    saldo_real = temp_api.balance
                    temp_api.disconnect()
            except:
                pass
        
        return jsonify({
            'success': True,
            'bot_running': True,
            'status': 'starting',
            'message': 'Bot iniciando, aguarde...',
            'balance': saldo_real,
            'saldo_liquido': 0.00,
            'win_rate': 0.0,
            'total_trades': 0,
            'trades': []
        })

    # Bot rodando - busca stats reais
    stats = {}

    if BOTS_AVAILABLE and bot and hasattr(bot, 'stop_loss'):
        try:
            stats = bot.stop_loss.get_estatisticas()
            
            if hasattr(bot, 'api'):
                try:
                    stats['balance'] = bot.api.balance
                    stats['currency'] = bot.api.currency
                except:
                    pass
            
            return jsonify({
                'success': True,
                'bot_running': True,
                'status': 'running',
                'balance': stats.get('saldo_atual', stats.get('balance', 10000.00)),
                'saldo_liquido': stats.get('saldo_liquido', stats.get('lucro_liquido', 0.00)),
                'win_rate': stats.get('win_rate', 0.0),
                'total_trades': stats.get('total_trades', 0),
                'wins': stats.get('vitorias', 0),
                'losses': stats.get('derrotas', 0),
                'trades': stats.get('trades', []),
                'mode': current_account_mode.upper()
            })
        except Exception as e:
            print(f"⚠️ Erro ao buscar stats reais: {e}")

    # Fallback
    return jsonify({
        'success': True,
        'bot_running': True,
        'status': status,
        'balance': 10000.00 if current_account_mode == 'demo' else 0.00,
        'saldo_liquido': 0.00,
        'win_rate': 0.0,
        'total_trades': 0,
        'wins': 0,
        'losses': 0,
        'trades': [],
        'mode': current_account_mode.upper()
    })

@app.route('/api/bot/trades/<bot_type>')
def get_bot_trades(bot_type):
    """
    Retorna lista de trades de um bot específico
    """
    if bot_type not in bots_state:
        return jsonify({'success': False, 'error': 'Bot não encontrado'}), 404

    state = bots_state[bot_type]
    bot = state.get('instance')

    trades = []

    if BOTS_AVAILABLE and bot and hasattr(bot, 'stop_loss'):
        try:
            stats = bot.stop_loss.get_estatisticas()
            trades = stats.get('trades', [])
        except Exception as e:
            print(f"⚠️ Erro ao buscar trades: {e}")

    return jsonify({
        'success': True,
        'trades': trades,
        'total': len(trades)
    })

@app.route('/api/bot/reset/<bot_type>', methods=['POST'])
def reset_bot(bot_type):
    """Reseta estado do bot"""
    if bot_type not in bots_state:
        return jsonify({'error': f'Bot {bot_type} não encontrado'}), 404
    
    bot = bots_state[bot_type].get('instance')
    if bot and hasattr(bot, 'stop'):
        try:
            bot.stop()
        except:
            pass
    
    bots_state[bot_type] = {
        'running': False,
        'instance': None,
        'thread': None,
        'status': 'stopped'
    }
    
    print(f"🔄 Bot {bot_type} resetado")
    
    return jsonify({
        'success': True,
        'message': f'Bot {bot_type} resetado com sucesso!'
    })

@app.route('/api/emergency/reset', methods=['POST'])
def emergency_reset():
    """Reset de emergência"""
    global bots_state

    for bot_type, state in bots_state.items():
        bot = state.get('instance')
        if bot and hasattr(bot, 'stop'):
            try:
                bot.stop()
            except:
                pass

    bots_state = {
        'manual': {'running': False, 'instance': None, 'thread': None, 'status': 'stopped'},
        'ia': {'running': False, 'instance': None, 'thread': None, 'status': 'stopped'},
        'ia_simples': {'running': False, 'instance': None, 'thread': None, 'status': 'stopped'},
        'ia_avancado': {'running': False, 'instance': None, 'thread': None, 'status': 'stopped'}
    }

    return jsonify({
        'success': True,
        'message': 'Estado resetado com sucesso!'
    })

# ==================== EXECUTAR ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    print("\n" + "=" * 70)
    print("🚀 ALPHA DOLAR 2.0 - API PRODUCTION (RENDER.COM)")
    print("✨ VERSÃO 2.0.7 - CORRIGIDA (FIX ESTADO INCONSISTENTE)")
    if BOTS_AVAILABLE:
        print("✅ BOTS PYTHON REAIS INTEGRADOS!")
    else:
        print("⚠️ MODO SIMULADO (Bots Python não disponíveis)")
    if CONFIG_LOADED:
        print("✅ CONFIG CARREGADO!")
    else:
        print("⚠️ CONFIG NÃO CARREGADO!")
    print(f"🔑 Token DEMO: {'✅' if DERIV_TOKEN_DEMO else '❌'}")
    print(f"🔑 Token REAL: {'✅' if DERIV_TOKEN_REAL else '❌'}")
    print(f"🎯 Modo atual: {current_account_mode.upper()}")
    print("=" * 70)
    print(f"🌐 Porta: {port}")
    print("=" * 70 + "\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
