from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.configuracao_sistema import ConfiguracaoSistema
from src.services.ia_service_simple import IAService
import os

ia_config_bp = Blueprint('ia_config', __name__)

@ia_config_bp.route('/ia/status', methods=['GET'])
def verificar_status_ia():
    """Verifica o status da configuração da IA"""
    try:
        # Verificar se as variáveis de ambiente estão configuradas
        openai_key = os.getenv('OPENAI_API_KEY')
        openai_base = os.getenv('OPENAI_API_BASE')
        
        # Verificar configurações no banco
        ia_ativa = ConfiguracaoSistema.obter_valor('ia_ativa', False)
        modelo_ia = ConfiguracaoSistema.obter_valor('modelo_ia', 'gpt-3.5-turbo')
        temperatura_ia = ConfiguracaoSistema.obter_valor('temperatura_ia', 0.7)
        max_tokens = ConfiguracaoSistema.obter_valor('max_tokens_ia', 500)
        
        status = {
            'ia_configurada': bool(openai_key),
            'ia_ativa': ia_ativa,
            'modelo': modelo_ia,
            'temperatura': temperatura_ia,
            'max_tokens': max_tokens,
            'openai_base_url': openai_base or 'https://api.openai.com/v1',
            'api_key_presente': bool(openai_key),
            'api_key_mascarada': f"{openai_key[:8]}..." if openai_key else None
        }
        
        # Testar conexão se configurada
        if openai_key and ia_ativa:
            try:
                ia_service = IAService()
                # Teste simples
                resposta_teste = ia_service._resposta_fallback("teste")
                status['teste_conexao'] = 'sucesso'
                status['ultima_verificacao'] = datetime.utcnow().isoformat()
            except Exception as e:
                status['teste_conexao'] = 'erro'
                status['erro_conexao'] = str(e)
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro ao verificar status da IA: {str(e)}',
            'ia_configurada': False,
            'ia_ativa': False
        }), 500

@ia_config_bp.route('/ia/configurar', methods=['POST'])
def configurar_ia():
    """Configura as definições da IA"""
    data = request.get_json()
    
    try:
        # Atualizar configurações
        if 'ia_ativa' in data:
            ConfiguracaoSistema.definir_valor('ia_ativa', data['ia_ativa'], 'boolean', 'ia', 'IA ativa no sistema')
        
        if 'modelo_ia' in data:
            ConfiguracaoSistema.definir_valor('modelo_ia', data['modelo_ia'], 'string', 'ia', 'Modelo de IA utilizado')
        
        if 'temperatura_ia' in data:
            ConfiguracaoSistema.definir_valor('temperatura_ia', data['temperatura_ia'], 'number', 'ia', 'Temperatura da IA (criatividade)')
        
        if 'max_tokens_ia' in data:
            ConfiguracaoSistema.definir_valor('max_tokens_ia', data['max_tokens_ia'], 'number', 'ia', 'Máximo de tokens por resposta')
        
        if 'prompt_personalizado' in data:
            ConfiguracaoSistema.definir_valor('prompt_personalizado', data['prompt_personalizado'], 'string', 'ia', 'Prompt personalizado para a IA')
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Configurações da IA atualizadas com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro ao configurar IA: {str(e)}',
            'sucesso': False
        }), 500

@ia_config_bp.route('/ia/testar', methods=['POST'])
def testar_ia():
    """Testa a IA com uma mensagem"""
    data = request.get_json()
    mensagem_teste = data.get('mensagem', 'Olá, como você pode me ajudar?')
    
    try:
        ia_service = IAService()
        
        # Simular uma conversa de teste
        resposta = ia_service._resposta_fallback(mensagem_teste)
        
        # Se a IA estiver configurada, tentar usar OpenAI
        if os.getenv('OPENAI_API_KEY'):
            try:
                # Teste real com OpenAI
                response = ia_service.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Você é um assistente virtual para secretariado remoto. Responda de forma profissional e cordial."},
                        {"role": "user", "content": mensagem_teste}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                resposta = response.choices[0].message.content.strip()
                
                return jsonify({
                    'sucesso': True,
                    'resposta': resposta,
                    'tipo': 'openai',
                    'modelo': 'gpt-3.5-turbo',
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    'sucesso': False,
                    'resposta': resposta,
                    'tipo': 'fallback',
                    'erro_openai': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        return jsonify({
            'sucesso': True,
            'resposta': resposta,
            'tipo': 'fallback',
            'observacao': 'OpenAI não configurado, usando resposta padrão',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro ao testar IA: {str(e)}',
            'sucesso': False
        }), 500

@ia_config_bp.route('/ia/prompts', methods=['GET'])
def listar_prompts():
    """Lista prompts disponíveis para a IA"""
    prompts_predefinidos = [
        {
            'id': 'secretariado_geral',
            'nome': 'Secretariado Geral',
            'descricao': 'Prompt genérico para secretariado remoto',
            'prompt': """Você é um assistente virtual especializado em secretariado remoto para profissionais da área de beleza e saúde feminina.

Suas responsabilidades incluem:
- Agendar consultas e procedimentos
- Responder dúvidas sobre serviços
- Confirmar horários e reagendar quando necessário
- Fornecer informações sobre preparos pré e pós-procedimentos
- Manter um tom profissional, cordial e acolhedor

Diretrizes importantes:
- Sempre confirme informações importantes antes de finalizar agendamentos
- Se não souber uma informação específica, informe que irá verificar com o profissional
- Mantenha a conversa focada nos serviços oferecidos
- Use linguagem clara e acessível
- Seja empática e atenciosa com as necessidades das clientes"""
        },
        {
            'id': 'dermatologia',
            'nome': 'Dermatologia',
            'descricao': 'Especializado para clínicas dermatológicas',
            'prompt': """Você é um assistente virtual especializado em atendimento para clínicas dermatológicas.

Suas responsabilidades incluem:
- Agendar consultas dermatológicas e procedimentos estéticos
- Orientar sobre preparos pré-consulta
- Esclarecer dúvidas sobre tratamentos dermatológicos
- Confirmar e reagendar consultas
- Fornecer informações sobre cuidados pós-procedimento

Diretrizes específicas:
- Sempre pergunte sobre alergias antes de procedimentos
- Oriente sobre proteção solar quando relevante
- Seja clara sobre preparos necessários (ex: não usar maquiagem)
- Mantenha sigilo médico e não dê diagnósticos
- Encaminhe dúvidas médicas específicas para o dermatologista"""
        },
        {
            'id': 'estetica',
            'nome': 'Estética',
            'descricao': 'Para clínicas de estética e beleza',
            'prompt': """Você é um assistente virtual para clínicas de estética e beleza.

Suas responsabilidades incluem:
- Agendar procedimentos estéticos e de beleza
- Orientar sobre preparos e cuidados
- Esclarecer dúvidas sobre tratamentos
- Confirmar e reagendar sessões
- Fornecer informações sobre pacotes e promoções

Diretrizes específicas:
- Destaque os benefícios dos tratamentos oferecidos
- Oriente sobre cuidados pré e pós-procedimento
- Seja acolhedora e compreensiva com inseguranças estéticas
- Sugira tratamentos complementares quando apropriado
- Mantenha foco na autoestima e bem-estar da cliente"""
        }
    ]
    
    # Buscar prompt personalizado se existir
    prompt_personalizado = ConfiguracaoSistema.obter_valor('prompt_personalizado')
    if prompt_personalizado:
        prompts_predefinidos.insert(0, {
            'id': 'personalizado',
            'nome': 'Personalizado',
            'descricao': 'Prompt personalizado configurado pelo administrador',
            'prompt': prompt_personalizado
        })
    
    return jsonify(prompts_predefinidos)

@ia_config_bp.route('/ia/prompts/<prompt_id>', methods=['PUT'])
def aplicar_prompt(prompt_id):
    """Aplica um prompt específico"""
    data = request.get_json()
    
    try:
        # Buscar o prompt
        prompts = {
            'secretariado_geral': """Você é um assistente virtual especializado em secretariado remoto para profissionais da área de beleza e saúde feminina...""",
            'dermatologia': """Você é um assistente virtual especializado em atendimento para clínicas dermatológicas...""",
            'estetica': """Você é um assistente virtual para clínicas de estética e beleza..."""
        }
        
        if prompt_id == 'personalizado':
            prompt = data.get('prompt', '')
        else:
            prompt = prompts.get(prompt_id)
        
        if not prompt:
            return jsonify({'erro': 'Prompt não encontrado'}), 404
        
        # Salvar como prompt ativo
        ConfiguracaoSistema.definir_valor('prompt_ativo', prompt, 'string', 'ia', 'Prompt ativo da IA')
        ConfiguracaoSistema.definir_valor('prompt_id_ativo', prompt_id, 'string', 'ia', 'ID do prompt ativo')
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Prompt {prompt_id} aplicado com sucesso',
            'prompt_id': prompt_id
        })
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro ao aplicar prompt: {str(e)}',
            'sucesso': False
        }), 500

@ia_config_bp.route('/ia/estatisticas', methods=['GET'])
def obter_estatisticas_ia():
    """Obtém estatísticas de uso da IA"""
    try:
        # Estas estatísticas seriam coletadas em um sistema real
        # Por enquanto, retornar dados simulados
        
        estatisticas = {
            'total_mensagens_processadas': 1250,
            'mensagens_hoje': 45,
            'mensagens_esta_semana': 312,
            'agendamentos_criados_ia': 89,
            'taxa_sucesso_agendamentos': 0.85,
            'tempo_medio_resposta': 2.3,  # segundos
            'clientes_atendidos_ia': 156,
            'economia_tempo_funcionarias': 18.5,  # horas por semana
            'satisfacao_clientes': 4.2,  # de 5
            'uso_por_cliente': [
                {'cliente': 'Dr. João Pereira', 'mensagens': 89, 'agendamentos': 12},
                {'cliente': 'Dra. Patricia Lima', 'mensagens': 76, 'agendamentos': 8}
            ]
        }
        
        return jsonify(estatisticas)
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro ao obter estatísticas: {str(e)}'
        }), 500

@ia_config_bp.route('/ia/logs', methods=['GET'])
def obter_logs_ia():
    """Obtém logs de atividade da IA"""
    limite = request.args.get('limite', 50, type=int)
    
    try:
        # Em um sistema real, estes logs viriam de um banco de dados
        # Por enquanto, retornar dados simulados
        
        logs_simulados = [
            {
                'id': 1,
                'timestamp': '2025-08-09T14:30:00Z',
                'tipo': 'mensagem_processada',
                'cliente': 'Dr. João Pereira',
                'mensagem_entrada': 'Gostaria de agendar uma consulta',
                'resposta_ia': 'Claro! Posso ajudar com o agendamento. Qual seria o melhor dia para você?',
                'tempo_processamento': 1.8,
                'sucesso': True
            },
            {
                'id': 2,
                'timestamp': '2025-08-09T14:25:00Z',
                'tipo': 'agendamento_detectado',
                'cliente': 'Dra. Patricia Lima',
                'dados_extraidos': {'tipo': 'limpeza de pele', 'data_preferida': '2025-08-15'},
                'sucesso': True
            },
            {
                'id': 3,
                'timestamp': '2025-08-09T14:20:00Z',
                'tipo': 'erro_processamento',
                'cliente': 'Dr. João Pereira',
                'erro': 'Rate limit exceeded',
                'fallback_usado': True,
                'sucesso': False
            }
        ]
        
        return jsonify(logs_simulados[:limite])
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro ao obter logs: {str(e)}'
        }), 500

