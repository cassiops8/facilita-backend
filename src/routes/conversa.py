from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.conversa import Conversa, Mensagem
from src.models.cliente import Cliente
from src.services.whatsapp_service import WhatsAppService
from src.services.ia_service_deploy import IAService

conversa_bp = Blueprint('conversa', __name__)
whatsapp_service = WhatsAppService()
ia_service = IAService()

@conversa_bp.route('/conversas', methods=['GET'])
def listar_conversas():
    """Lista todas as conversas"""
    cliente_id = request.args.get('cliente_id')
    funcionaria_id = request.args.get('funcionaria_id')
    ativas_apenas = request.args.get('ativas_apenas', 'false').lower() == 'true'
    
    query = Conversa.query
    
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    
    if funcionaria_id:
        # Filtrar por funcionária através do cliente
        clientes_funcionaria = Cliente.query.filter_by(funcionaria_id=funcionaria_id).all()
        cliente_ids = [c.id for c in clientes_funcionaria]
        query = query.filter(Conversa.cliente_id.in_(cliente_ids))
    
    if ativas_apenas:
        query = query.filter_by(ativa=True)
    
    conversas = query.order_by(Conversa.ultima_atividade.desc()).all()
    return jsonify([c.to_dict() for c in conversas])

@conversa_bp.route('/conversas', methods=['POST'])
def criar_conversa():
    """Cria uma nova conversa"""
    data = request.get_json()
    
    conversa = Conversa(
        numero_whatsapp=data['numero_whatsapp'],
        nome_contato=data['nome_contato'],
        cliente_id=data['cliente_id'],
        modo_ia=data.get('modo_ia', True)
    )
    
    db.session.add(conversa)
    db.session.commit()
    
    return jsonify(conversa.to_dict()), 201

@conversa_bp.route('/conversas/<int:conversa_id>', methods=['GET'])
def obter_conversa(conversa_id):
    """Obtém uma conversa específica"""
    conversa = Conversa.query.get_or_404(conversa_id)
    return jsonify(conversa.to_dict())

@conversa_bp.route('/conversas/<int:conversa_id>', methods=['PUT'])
def atualizar_conversa(conversa_id):
    """Atualiza uma conversa"""
    conversa = Conversa.query.get_or_404(conversa_id)
    data = request.get_json()
    
    conversa.nome_contato = data.get('nome_contato', conversa.nome_contato)
    conversa.ativa = data.get('ativa', conversa.ativa)
    conversa.modo_ia = data.get('modo_ia', conversa.modo_ia)
    
    db.session.commit()
    return jsonify(conversa.to_dict())

@conversa_bp.route('/conversas/<int:conversa_id>/mensagens', methods=['GET'])
def listar_mensagens(conversa_id):
    """Lista todas as mensagens de uma conversa"""
    conversa = Conversa.query.get_or_404(conversa_id)
    mensagens = Mensagem.query.filter_by(conversa_id=conversa_id).order_by(Mensagem.data_envio.asc()).all()
    return jsonify([m.to_dict() for m in mensagens])

@conversa_bp.route('/conversas/<int:conversa_id>/mensagens', methods=['POST'])
def enviar_mensagem():
    """Envia uma nova mensagem"""
    conversa_id = request.view_args['conversa_id']
    data = request.get_json()
    
    conversa = Conversa.query.get_or_404(conversa_id)
    
    # Se for mensagem de funcionária, enviar via WhatsApp
    if data['remetente'] == 'funcionaria':
        sucesso = whatsapp_service.enviar_mensagem_funcionaria(
            conversa_id, 
            data['conteudo'], 
            data.get('funcionaria_id')
        )
        if not sucesso:
            return jsonify({'erro': 'Erro ao enviar mensagem'}), 500
    else:
        # Salvar mensagem diretamente
        mensagem = Mensagem(
            conteudo=data['conteudo'],
            tipo=data.get('tipo', 'texto'),
            remetente=data['remetente'],
            conversa_id=conversa_id,
            funcionaria_id=data.get('funcionaria_id')
        )
        
        db.session.add(mensagem)
        
        # Atualizar última atividade da conversa
        conversa.ultima_atividade = datetime.utcnow()
        
        db.session.commit()
    
    # Recarregar mensagens para retornar a lista atualizada
    mensagens = Mensagem.query.filter_by(conversa_id=conversa_id).order_by(Mensagem.data_envio.asc()).all()
    return jsonify([m.to_dict() for m in mensagens])

@conversa_bp.route('/conversas/<int:conversa_id>/modo-ia', methods=['PUT'])
def alternar_modo_ia(conversa_id):
    """Alterna entre modo IA e modo manual"""
    data = request.get_json()
    
    sucesso = whatsapp_service.alternar_modo_ia(conversa_id, data['modo_ia'])
    
    if sucesso:
        conversa = Conversa.query.get(conversa_id)
        return jsonify(conversa.to_dict())
    else:
        return jsonify({'erro': 'Conversa não encontrada'}), 404

@conversa_bp.route('/webhook/whatsapp', methods=['GET'])
def verificar_webhook():
    """Verificação do webhook do WhatsApp"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    # Token de verificação (configurar em produção)
    verify_token = "facilita_webhook_token"
    
    if mode == 'subscribe' and token == verify_token:
        return challenge
    else:
        return 'Forbidden', 403

@conversa_bp.route('/webhook/whatsapp', methods=['POST'])
def webhook_whatsapp():
    """Webhook para receber mensagens do WhatsApp"""
    data = request.get_json()
    
    sucesso = whatsapp_service.processar_webhook(data)
    
    if sucesso:
        return jsonify({'status': 'sucesso'}), 200
    else:
        return jsonify({'status': 'erro'}), 400

@conversa_bp.route('/whatsapp/enviar', methods=['POST'])
def enviar_whatsapp():
    """Envia mensagem via WhatsApp"""
    data = request.get_json()
    
    sucesso = whatsapp_service.enviar_mensagem(data['numero'], data['mensagem'])
    
    if sucesso:
        return jsonify({
            'status': 'enviado',
            'numero': data['numero'],
            'mensagem': data['mensagem']
        }), 200
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Falha ao enviar'}), 500

@conversa_bp.route('/ia/processar', methods=['POST'])
def processar_ia():
    """Processa uma mensagem com IA (para testes)"""
    data = request.get_json()
    
    resposta = ia_service.processar_mensagem(
        data['conversa_id'], 
        data['mensagem']
    )
    
    return jsonify({'resposta': resposta})

