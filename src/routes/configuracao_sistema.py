from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.configuracao_sistema import ConfiguracaoSistema, InstanciaWhitelabel
import os
import base64

configuracao_sistema_bp = Blueprint('configuracao_sistema', __name__)

# ===== ROTAS PARA CONFIGURAÇÕES GERAIS =====

@configuracao_sistema_bp.route('/configuracoes', methods=['GET'])
def listar_configuracoes():
    """Lista todas as configurações do sistema"""
    categoria = request.args.get('categoria')
    
    query = ConfiguracaoSistema.query
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    configs = query.order_by(ConfiguracaoSistema.categoria, ConfiguracaoSistema.chave).all()
    
    # Agrupar por categoria
    resultado = {}
    for config in configs:
        if config.categoria not in resultado:
            resultado[config.categoria] = []
        resultado[config.categoria].append(config.to_dict())
    
    return jsonify(resultado)

@configuracao_sistema_bp.route('/configuracoes/<chave>', methods=['GET'])
def obter_configuracao(chave):
    """Obtém uma configuração específica"""
    config = ConfiguracaoSistema.query.filter_by(chave=chave).first()
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404
    
    return jsonify(config.to_dict())

@configuracao_sistema_bp.route('/configuracoes/<chave>', methods=['PUT'])
def atualizar_configuracao(chave):
    """Atualiza uma configuração"""
    data = request.get_json()
    
    config = ConfiguracaoSistema.query.filter_by(chave=chave).first()
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404
    
    if not config.editavel:
        return jsonify({'erro': 'Esta configuração não pode ser editada'}), 403
    
    config.set_valor(data['valor'])
    config.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    return jsonify(config.to_dict())

@configuracao_sistema_bp.route('/configuracoes', methods=['POST'])
def criar_configuracao():
    """Cria uma nova configuração"""
    data = request.get_json()
    
    # Verificar se já existe
    config_existente = ConfiguracaoSistema.query.filter_by(chave=data['chave']).first()
    if config_existente:
        return jsonify({'erro': 'Configuração já existe'}), 400
    
    config = ConfiguracaoSistema(
        chave=data['chave'],
        tipo=data.get('tipo', 'string'),
        categoria=data.get('categoria', 'geral'),
        descricao=data.get('descricao'),
        editavel=data.get('editavel', True)
    )
    config.set_valor(data['valor'])
    
    db.session.add(config)
    db.session.commit()
    
    return jsonify(config.to_dict()), 201

@configuracao_sistema_bp.route('/configuracoes/lote', methods=['PUT'])
def atualizar_configuracoes_lote():
    """Atualiza múltiplas configurações de uma vez"""
    data = request.get_json()
    configuracoes = data.get('configuracoes', [])
    
    resultados = []
    
    for item in configuracoes:
        chave = item['chave']
        valor = item['valor']
        
        config = ConfiguracaoSistema.query.filter_by(chave=chave).first()
        if config and config.editavel:
            config.set_valor(valor)
            config.data_atualizacao = datetime.utcnow()
            resultados.append({'chave': chave, 'sucesso': True})
        else:
            resultados.append({'chave': chave, 'sucesso': False, 'erro': 'Não encontrada ou não editável'})
    
    db.session.commit()
    return jsonify({'resultados': resultados})

# ===== ROTAS PARA UPLOAD DE LOGO =====

@configuracao_sistema_bp.route('/configuracoes/upload-logo', methods=['POST'])
def upload_logo():
    """Faz upload de uma nova logo"""
    if 'logo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
    
    arquivo = request.files['logo']
    if arquivo.filename == '':
        return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400
    
    # Verificar tipo de arquivo
    tipos_permitidos = {'png', 'jpg', 'jpeg', 'svg', 'webp'}
    extensao = arquivo.filename.rsplit('.', 1)[1].lower() if '.' in arquivo.filename else ''
    
    if extensao not in tipos_permitidos:
        return jsonify({'erro': 'Tipo de arquivo não permitido'}), 400
    
    # Criar diretório se não existir
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Salvar arquivo
    nome_arquivo = f"logo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extensao}"
    caminho_arquivo = os.path.join(upload_dir, nome_arquivo)
    arquivo.save(caminho_arquivo)
    
    # Atualizar configuração
    url_logo = f"/static/uploads/{nome_arquivo}"
    ConfiguracaoSistema.definir_valor('logo_url', url_logo, 'string', 'aparencia', 'URL da logo do sistema')
    
    return jsonify({
        'sucesso': True,
        'url_logo': url_logo,
        'nome_arquivo': nome_arquivo
    })

# ===== ROTAS PARA APARÊNCIA =====

@configuracao_sistema_bp.route('/configuracoes/aparencia', methods=['GET'])
def obter_configuracoes_aparencia():
    """Obtém todas as configurações de aparência"""
    configs = ConfiguracaoSistema.query.filter_by(categoria='aparencia').all()
    
    resultado = {}
    for config in configs:
        resultado[config.chave] = config.to_dict()['valor']
    
    # Valores padrão se não existirem
    padroes = {
        'logo_url': '/static/logo-facilita.png',
        'nome_sistema': 'Facilita AR',
        'cor_primaria': '#8B4513',
        'cor_secundaria': '#D4C1A5',
        'cor_fundo': '#FFFFFF',
        'cor_texto': '#000000',
        'cor_accent': '#8B4513',
        'tema_escuro': False,
        'favicon_url': '/static/favicon.ico'
    }
    
    for chave, valor_padrao in padroes.items():
        if chave not in resultado:
            resultado[chave] = valor_padrao
    
    return jsonify(resultado)

@configuracao_sistema_bp.route('/configuracoes/aparencia', methods=['PUT'])
def atualizar_aparencia():
    """Atualiza configurações de aparência"""
    data = request.get_json()
    
    # Configurações permitidas para aparência
    configs_aparencia = [
        'nome_sistema', 'cor_primaria', 'cor_secundaria', 'cor_fundo', 
        'cor_texto', 'cor_accent', 'tema_escuro', 'favicon_url'
    ]
    
    for chave in configs_aparencia:
        if chave in data:
            tipo = 'boolean' if chave == 'tema_escuro' else 'string'
            ConfiguracaoSistema.definir_valor(
                chave, 
                data[chave], 
                tipo, 
                'aparencia', 
                f'Configuração de aparência: {chave}'
            )
    
    return jsonify({'sucesso': True, 'mensagem': 'Configurações de aparência atualizadas'})

# ===== ROTAS PARA WHITELABEL =====

@configuracao_sistema_bp.route('/whitelabel/instancias', methods=['GET'])
def listar_instancias_whitelabel():
    """Lista todas as instâncias whitelabel"""
    instancias = InstanciaWhitelabel.query.order_by(InstanciaWhitelabel.data_criacao.desc()).all()
    return jsonify([instancia.to_dict() for instancia in instancias])

@configuracao_sistema_bp.route('/whitelabel/instancias', methods=['POST'])
def criar_instancia_whitelabel():
    """Cria uma nova instância whitelabel"""
    data = request.get_json()
    
    # Verificar se subdomínio já existe
    instancia_existente = InstanciaWhitelabel.query.filter_by(subdominio=data['subdominio']).first()
    if instancia_existente:
        return jsonify({'erro': 'Subdomínio já existe'}), 400
    
    instancia = InstanciaWhitelabel(
        nome=data['nome'],
        subdominio=data['subdominio'],
        logo_url=data.get('logo_url'),
        ativa=data.get('ativa', True)
    )
    
    if 'cores_personalizadas' in data:
        instancia.set_cores(data['cores_personalizadas'])
    
    if 'configuracoes_personalizadas' in data:
        instancia.set_configuracoes(data['configuracoes_personalizadas'])
    
    db.session.add(instancia)
    db.session.commit()
    
    return jsonify(instancia.to_dict()), 201

@configuracao_sistema_bp.route('/whitelabel/instancias/<int:instancia_id>', methods=['GET'])
def obter_instancia_whitelabel(instancia_id):
    """Obtém uma instância whitelabel específica"""
    instancia = InstanciaWhitelabel.query.get_or_404(instancia_id)
    return jsonify(instancia.to_dict())

@configuracao_sistema_bp.route('/whitelabel/instancias/<int:instancia_id>', methods=['PUT'])
def atualizar_instancia_whitelabel(instancia_id):
    """Atualiza uma instância whitelabel"""
    instancia = InstanciaWhitelabel.query.get_or_404(instancia_id)
    data = request.get_json()
    
    # Verificar se novo subdomínio já existe
    if 'subdominio' in data and data['subdominio'] != instancia.subdominio:
        instancia_existente = InstanciaWhitelabel.query.filter_by(subdominio=data['subdominio']).first()
        if instancia_existente:
            return jsonify({'erro': 'Subdomínio já existe'}), 400
    
    # Atualizar campos
    instancia.nome = data.get('nome', instancia.nome)
    instancia.subdominio = data.get('subdominio', instancia.subdominio)
    instancia.logo_url = data.get('logo_url', instancia.logo_url)
    instancia.ativa = data.get('ativa', instancia.ativa)
    
    if 'cores_personalizadas' in data:
        instancia.set_cores(data['cores_personalizadas'])
    
    if 'configuracoes_personalizadas' in data:
        instancia.set_configuracoes(data['configuracoes_personalizadas'])
    
    instancia.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    return jsonify(instancia.to_dict())

@configuracao_sistema_bp.route('/whitelabel/instancias/<int:instancia_id>', methods=['DELETE'])
def deletar_instancia_whitelabel(instancia_id):
    """Deleta uma instância whitelabel"""
    instancia = InstanciaWhitelabel.query.get_or_404(instancia_id)
    
    db.session.delete(instancia)
    db.session.commit()
    
    return jsonify({'mensagem': 'Instância deletada com sucesso'})

@configuracao_sistema_bp.route('/whitelabel/instancias/<int:instancia_id>/toggle', methods=['PUT'])
def toggle_instancia_whitelabel(instancia_id):
    """Ativa/desativa uma instância whitelabel"""
    instancia = InstanciaWhitelabel.query.get_or_404(instancia_id)
    
    instancia.ativa = not instancia.ativa
    instancia.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'mensagem': f'Instância {"ativada" if instancia.ativa else "desativada"} com sucesso',
        'instancia': instancia.to_dict()
    })

# ===== ROTAS PARA EXPORTAR/IMPORTAR CONFIGURAÇÕES =====

@configuracao_sistema_bp.route('/configuracoes/exportar', methods=['GET'])
def exportar_configuracoes():
    """Exporta todas as configurações do sistema"""
    configs = ConfiguracaoSistema.query.all()
    instancias = InstanciaWhitelabel.query.all()
    
    dados_exportacao = {
        'configuracoes': [config.to_dict() for config in configs],
        'instancias_whitelabel': [instancia.to_dict() for instancia in instancias],
        'data_exportacao': datetime.utcnow().isoformat(),
        'versao': '1.0'
    }
    
    return jsonify(dados_exportacao)

@configuracao_sistema_bp.route('/configuracoes/importar', methods=['POST'])
def importar_configuracoes():
    """Importa configurações do sistema"""
    data = request.get_json()
    
    if 'configuracoes' not in data:
        return jsonify({'erro': 'Dados de configuração não encontrados'}), 400
    
    configs_importadas = 0
    instancias_importadas = 0
    
    # Importar configurações
    for config_data in data.get('configuracoes', []):
        chave = config_data['chave']
        config = ConfiguracaoSistema.query.filter_by(chave=chave).first()
        
        if config:
            config.set_valor(config_data['valor'])
            config.data_atualizacao = datetime.utcnow()
        else:
            config = ConfiguracaoSistema(
                chave=chave,
                tipo=config_data.get('tipo', 'string'),
                categoria=config_data.get('categoria', 'geral'),
                descricao=config_data.get('descricao'),
                editavel=config_data.get('editavel', True)
            )
            config.set_valor(config_data['valor'])
            db.session.add(config)
        
        configs_importadas += 1
    
    # Importar instâncias whitelabel (opcional)
    for instancia_data in data.get('instancias_whitelabel', []):
        subdominio = instancia_data['subdominio']
        instancia = InstanciaWhitelabel.query.filter_by(subdominio=subdominio).first()
        
        if not instancia:
            instancia = InstanciaWhitelabel(
                nome=instancia_data['nome'],
                subdominio=subdominio,
                logo_url=instancia_data.get('logo_url'),
                ativa=instancia_data.get('ativa', True)
            )
            instancia.set_cores(instancia_data.get('cores_personalizadas', {}))
            instancia.set_configuracoes(instancia_data.get('configuracoes_personalizadas', {}))
            db.session.add(instancia)
            instancias_importadas += 1
    
    db.session.commit()
    
    return jsonify({
        'sucesso': True,
        'configuracoes_importadas': configs_importadas,
        'instancias_importadas': instancias_importadas
    })

