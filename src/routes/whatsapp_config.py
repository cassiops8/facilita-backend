from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.whatsapp_config import WhatsAppConfig
from src.models.cliente import Cliente

whatsapp_config_bp = Blueprint('whatsapp_config', __name__)

@whatsapp_config_bp.route('/whatsapp-configs', methods=['GET'])
def listar_whatsapp_configs():
    """Lista todas as configurações de WhatsApp"""
    cliente_id = request.args.get('cliente_id')
    ativas_apenas = request.args.get('ativas_apenas', 'false').lower() == 'true'
    
    query = WhatsAppConfig.query
    
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    
    if ativas_apenas:
        query = query.filter_by(ativo=True)
    
    configs = query.order_by(WhatsAppConfig.data_criacao.desc()).all()
    return jsonify([config.to_dict() for config in configs])

@whatsapp_config_bp.route('/whatsapp-configs', methods=['POST'])
def criar_whatsapp_config():
    """Cria uma nova configuração de WhatsApp"""
    data = request.get_json()
    
    # Verificar se o cliente existe
    cliente = Cliente.query.get(data['cliente_id'])
    if not cliente:
        return jsonify({'erro': 'Cliente não encontrado'}), 404
    
    # Verificar se já existe configuração para este número
    config_existente = WhatsAppConfig.query.filter_by(
        numero_whatsapp=data['numero_whatsapp']
    ).first()
    
    if config_existente:
        return jsonify({'erro': 'Já existe uma configuração para este número'}), 400
    
    config = WhatsAppConfig(
        cliente_id=data['cliente_id'],
        numero_whatsapp=data['numero_whatsapp'],
        nome_exibicao=data['nome_exibicao'],
        token_acesso=data.get('token_acesso'),
        phone_number_id=data.get('phone_number_id'),
        webhook_verify_token=data.get('webhook_verify_token'),
        ativo=data.get('ativo', True)
    )
    
    db.session.add(config)
    db.session.commit()
    
    return jsonify(config.to_dict()), 201

@whatsapp_config_bp.route('/whatsapp-configs/<int:config_id>', methods=['GET'])
def obter_whatsapp_config(config_id):
    """Obtém uma configuração específica de WhatsApp"""
    config = WhatsAppConfig.query.get_or_404(config_id)
    return jsonify(config.to_dict())

@whatsapp_config_bp.route('/whatsapp-configs/<int:config_id>', methods=['PUT'])
def atualizar_whatsapp_config(config_id):
    """Atualiza uma configuração de WhatsApp"""
    config = WhatsAppConfig.query.get_or_404(config_id)
    data = request.get_json()
    
    # Verificar se o novo número já está em uso por outra configuração
    if 'numero_whatsapp' in data and data['numero_whatsapp'] != config.numero_whatsapp:
        config_existente = WhatsAppConfig.query.filter_by(
            numero_whatsapp=data['numero_whatsapp']
        ).first()
        
        if config_existente:
            return jsonify({'erro': 'Já existe uma configuração para este número'}), 400
    
    # Atualizar campos
    config.numero_whatsapp = data.get('numero_whatsapp', config.numero_whatsapp)
    config.nome_exibicao = data.get('nome_exibicao', config.nome_exibicao)
    config.token_acesso = data.get('token_acesso', config.token_acesso)
    config.phone_number_id = data.get('phone_number_id', config.phone_number_id)
    config.webhook_verify_token = data.get('webhook_verify_token', config.webhook_verify_token)
    config.ativo = data.get('ativo', config.ativo)
    config.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    return jsonify(config.to_dict())

@whatsapp_config_bp.route('/whatsapp-configs/<int:config_id>', methods=['DELETE'])
def deletar_whatsapp_config(config_id):
    """Deleta uma configuração de WhatsApp"""
    config = WhatsAppConfig.query.get_or_404(config_id)
    
    db.session.delete(config)
    db.session.commit()
    
    return jsonify({'mensagem': 'Configuração deletada com sucesso'}), 200

@whatsapp_config_bp.route('/whatsapp-configs/<int:config_id>/toggle', methods=['PUT'])
def toggle_whatsapp_config(config_id):
    """Ativa/desativa uma configuração de WhatsApp"""
    config = WhatsAppConfig.query.get_or_404(config_id)
    
    config.ativo = not config.ativo
    config.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'mensagem': f'Configuração {"ativada" if config.ativo else "desativada"} com sucesso',
        'config': config.to_dict()
    })

@whatsapp_config_bp.route('/whatsapp-configs/por-numero/<numero>', methods=['GET'])
def obter_config_por_numero(numero):
    """Obtém configuração de WhatsApp por número"""
    config = WhatsAppConfig.query.filter_by(
        numero_whatsapp=numero,
        ativo=True
    ).first()
    
    if not config:
        return jsonify({'erro': 'Configuração não encontrada para este número'}), 404
    
    return jsonify(config.to_dict())

@whatsapp_config_bp.route('/whatsapp-configs/testar/<int:config_id>', methods=['POST'])
def testar_whatsapp_config(config_id):
    """Testa uma configuração de WhatsApp"""
    config = WhatsAppConfig.query.get_or_404(config_id)
    data = request.get_json()
    
    numero_teste = data.get('numero_teste')
    mensagem_teste = data.get('mensagem_teste', 'Teste de configuração do WhatsApp')
    
    if not numero_teste:
        return jsonify({'erro': 'Número de teste é obrigatório'}), 400
    
    # Aqui seria implementada a lógica real de teste
    # Por enquanto, simular sucesso
    
    return jsonify({
        'sucesso': True,
        'mensagem': 'Teste realizado com sucesso',
        'detalhes': {
            'numero_origem': config.numero_whatsapp,
            'numero_destino': numero_teste,
            'mensagem': mensagem_teste,
            'timestamp': datetime.utcnow().isoformat()
        }
    })

