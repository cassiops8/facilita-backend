from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.chat_interno import GrupoChat, MembroGrupo, MensagemChat, StatusLeitura
from src.models.funcionaria import Funcionaria

chat_interno_bp = Blueprint('chat_interno', __name__)

# ===== ROTAS PARA GRUPOS =====

@chat_interno_bp.route('/chat/grupos', methods=['GET'])
def listar_grupos():
    """Lista todos os grupos de chat que a funcionária tem acesso"""
    funcionaria_id = request.args.get('funcionaria_id')
    
    if not funcionaria_id:
        return jsonify({'erro': 'funcionaria_id é obrigatório'}), 400
    
    # Buscar grupos onde a funcionária é membro
    membros = MembroGrupo.query.filter_by(
        funcionaria_id=funcionaria_id,
        ativo=True
    ).all()
    
    grupos = []
    for membro in membros:
        if membro.grupo and membro.grupo.ativo:
            grupo_dict = membro.grupo.to_dict()
            grupo_dict['meu_papel'] = membro.papel
            grupo_dict['notificacoes'] = membro.notificacoes
            grupos.append(grupo_dict)
    
    return jsonify(grupos)

@chat_interno_bp.route('/chat/grupos', methods=['POST'])
def criar_grupo():
    """Cria um novo grupo de chat"""
    data = request.get_json()
    
    grupo = GrupoChat(
        nome=data['nome'],
        descricao=data.get('descricao', ''),
        tipo=data.get('tipo', 'grupo'),
        privado=data.get('privado', False),
        cor=data.get('cor', '#8B4513'),
        icone=data.get('icone', 'MessageCircle'),
        criado_por=data['criado_por']
    )
    
    db.session.add(grupo)
    db.session.flush()  # Para obter o ID do grupo
    
    # Adicionar o criador como admin do grupo
    membro_criador = MembroGrupo(
        grupo_id=grupo.id,
        funcionaria_id=data['criado_por'],
        papel='admin'
    )
    
    db.session.add(membro_criador)
    
    # Adicionar outros membros se especificados
    if 'membros' in data:
        for membro_id in data['membros']:
            if membro_id != data['criado_por']:  # Não duplicar o criador
                membro = MembroGrupo(
                    grupo_id=grupo.id,
                    funcionaria_id=membro_id,
                    papel='membro'
                )
                db.session.add(membro)
    
    db.session.commit()
    
    return jsonify(grupo.to_dict()), 201

@chat_interno_bp.route('/chat/grupos/<int:grupo_id>', methods=['GET'])
def obter_grupo(grupo_id):
    """Obtém detalhes de um grupo específico"""
    grupo = GrupoChat.query.get_or_404(grupo_id)
    return jsonify(grupo.to_dict())

@chat_interno_bp.route('/chat/grupos/<int:grupo_id>', methods=['PUT'])
def atualizar_grupo(grupo_id):
    """Atualiza um grupo de chat"""
    grupo = GrupoChat.query.get_or_404(grupo_id)
    data = request.get_json()
    
    grupo.nome = data.get('nome', grupo.nome)
    grupo.descricao = data.get('descricao', grupo.descricao)
    grupo.cor = data.get('cor', grupo.cor)
    grupo.icone = data.get('icone', grupo.icone)
    grupo.privado = data.get('privado', grupo.privado)
    grupo.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    return jsonify(grupo.to_dict())

@chat_interno_bp.route('/chat/grupos/<int:grupo_id>/membros', methods=['GET'])
def listar_membros_grupo(grupo_id):
    """Lista todos os membros de um grupo"""
    membros = MembroGrupo.query.filter_by(
        grupo_id=grupo_id,
        ativo=True
    ).all()
    
    return jsonify([membro.to_dict() for membro in membros])

@chat_interno_bp.route('/chat/grupos/<int:grupo_id>/membros', methods=['POST'])
def adicionar_membro_grupo(grupo_id):
    """Adiciona um membro ao grupo"""
    data = request.get_json()
    
    # Verificar se já é membro
    membro_existente = MembroGrupo.query.filter_by(
        grupo_id=grupo_id,
        funcionaria_id=data['funcionaria_id']
    ).first()
    
    if membro_existente:
        if membro_existente.ativo:
            return jsonify({'erro': 'Funcionária já é membro do grupo'}), 400
        else:
            # Reativar membro
            membro_existente.ativo = True
            membro_existente.data_entrada = datetime.utcnow()
            db.session.commit()
            return jsonify(membro_existente.to_dict())
    
    membro = MembroGrupo(
        grupo_id=grupo_id,
        funcionaria_id=data['funcionaria_id'],
        papel=data.get('papel', 'membro')
    )
    
    db.session.add(membro)
    db.session.commit()
    
    return jsonify(membro.to_dict()), 201

@chat_interno_bp.route('/chat/grupos/<int:grupo_id>/membros/<int:membro_id>', methods=['DELETE'])
def remover_membro_grupo(grupo_id, membro_id):
    """Remove um membro do grupo"""
    membro = MembroGrupo.query.filter_by(
        grupo_id=grupo_id,
        funcionaria_id=membro_id
    ).first_or_404()
    
    membro.ativo = False
    db.session.commit()
    
    return jsonify({'mensagem': 'Membro removido com sucesso'})

# ===== ROTAS PARA MENSAGENS =====

@chat_interno_bp.route('/chat/grupos/<int:grupo_id>/mensagens', methods=['GET'])
def listar_mensagens(grupo_id):
    """Lista mensagens de um grupo"""
    limite = request.args.get('limite', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    mensagens = MensagemChat.query.filter_by(
        grupo_id=grupo_id
    ).order_by(MensagemChat.data_envio.desc()).limit(limite).offset(offset).all()
    
    # Reverter para ordem cronológica
    mensagens.reverse()
    
    return jsonify([mensagem.to_dict() for mensagem in mensagens])

@chat_interno_bp.route('/chat/grupos/<int:grupo_id>/mensagens', methods=['POST'])
def enviar_mensagem(grupo_id):
    """Envia uma mensagem para o grupo"""
    data = request.get_json()
    
    mensagem = MensagemChat(
        grupo_id=grupo_id,
        remetente_id=data['remetente_id'],
        conteudo=data['conteudo'],
        tipo=data.get('tipo', 'texto'),
        arquivo_url=data.get('arquivo_url'),
        arquivo_nome=data.get('arquivo_nome'),
        resposta_para=data.get('resposta_para')
    )
    
    db.session.add(mensagem)
    db.session.flush()
    
    # Criar status de leitura para todos os membros do grupo
    membros = MembroGrupo.query.filter_by(
        grupo_id=grupo_id,
        ativo=True
    ).all()
    
    for membro in membros:
        status = StatusLeitura(
            mensagem_id=mensagem.id,
            funcionaria_id=membro.funcionaria_id,
            lida=(membro.funcionaria_id == data['remetente_id'])  # Marcar como lida para o remetente
        )
        if membro.funcionaria_id == data['remetente_id']:
            status.data_leitura = datetime.utcnow()
        
        db.session.add(status)
    
    db.session.commit()
    
    return jsonify(mensagem.to_dict()), 201

@chat_interno_bp.route('/chat/mensagens/<int:mensagem_id>', methods=['PUT'])
def editar_mensagem(mensagem_id):
    """Edita uma mensagem"""
    mensagem = MensagemChat.query.get_or_404(mensagem_id)
    data = request.get_json()
    
    # Verificar se o usuário pode editar (é o remetente)
    if mensagem.remetente_id != data.get('editor_id'):
        return jsonify({'erro': 'Você só pode editar suas próprias mensagens'}), 403
    
    mensagem.conteudo = data['conteudo']
    mensagem.editada = True
    mensagem.data_edicao = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(mensagem.to_dict())

@chat_interno_bp.route('/chat/mensagens/<int:mensagem_id>/marcar-lida', methods=['PUT'])
def marcar_mensagem_lida(mensagem_id):
    """Marca uma mensagem como lida"""
    data = request.get_json()
    funcionaria_id = data['funcionaria_id']
    
    status = StatusLeitura.query.filter_by(
        mensagem_id=mensagem_id,
        funcionaria_id=funcionaria_id
    ).first()
    
    if status:
        status.lida = True
        status.data_leitura = datetime.utcnow()
        db.session.commit()
        return jsonify(status.to_dict())
    
    return jsonify({'erro': 'Status de leitura não encontrado'}), 404

@chat_interno_bp.route('/chat/grupos/<int:grupo_id>/marcar-todas-lidas', methods=['PUT'])
def marcar_todas_mensagens_lidas(grupo_id):
    """Marca todas as mensagens de um grupo como lidas"""
    data = request.get_json()
    funcionaria_id = data['funcionaria_id']
    
    # Buscar todas as mensagens não lidas do grupo
    status_nao_lidos = db.session.query(StatusLeitura).join(MensagemChat).filter(
        MensagemChat.grupo_id == grupo_id,
        StatusLeitura.funcionaria_id == funcionaria_id,
        StatusLeitura.lida == False
    ).all()
    
    for status in status_nao_lidos:
        status.lida = True
        status.data_leitura = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'mensagem': f'{len(status_nao_lidos)} mensagens marcadas como lidas'})

# ===== ROTAS PARA ESTATÍSTICAS =====

@chat_interno_bp.route('/chat/estatisticas/<int:funcionaria_id>', methods=['GET'])
def obter_estatisticas_chat(funcionaria_id):
    """Obtém estatísticas do chat para uma funcionária"""
    
    # Total de grupos
    total_grupos = MembroGrupo.query.filter_by(
        funcionaria_id=funcionaria_id,
        ativo=True
    ).count()
    
    # Mensagens não lidas
    mensagens_nao_lidas = db.session.query(StatusLeitura).join(MensagemChat).join(GrupoChat).join(MembroGrupo).filter(
        MembroGrupo.funcionaria_id == funcionaria_id,
        MembroGrupo.ativo == True,
        StatusLeitura.funcionaria_id == funcionaria_id,
        StatusLeitura.lida == False
    ).count()
    
    # Grupos com mensagens não lidas
    grupos_com_nao_lidas = db.session.query(GrupoChat.id).join(MensagemChat).join(StatusLeitura).join(MembroGrupo).filter(
        MembroGrupo.funcionaria_id == funcionaria_id,
        MembroGrupo.ativo == True,
        StatusLeitura.funcionaria_id == funcionaria_id,
        StatusLeitura.lida == False
    ).distinct().count()
    
    return jsonify({
        'total_grupos': total_grupos,
        'mensagens_nao_lidas': mensagens_nao_lidas,
        'grupos_com_nao_lidas': grupos_com_nao_lidas
    })

# ===== ROTAS PARA BUSCA =====

@chat_interno_bp.route('/chat/buscar', methods=['GET'])
def buscar_mensagens():
    """Busca mensagens nos grupos da funcionária"""
    funcionaria_id = request.args.get('funcionaria_id')
    termo = request.args.get('termo', '')
    grupo_id = request.args.get('grupo_id')
    
    if not funcionaria_id or not termo:
        return jsonify({'erro': 'funcionaria_id e termo são obrigatórios'}), 400
    
    # Buscar apenas nos grupos onde a funcionária é membro
    query = db.session.query(MensagemChat).join(GrupoChat).join(MembroGrupo).filter(
        MembroGrupo.funcionaria_id == funcionaria_id,
        MembroGrupo.ativo == True,
        MensagemChat.conteudo.contains(termo)
    )
    
    if grupo_id:
        query = query.filter(MensagemChat.grupo_id == grupo_id)
    
    mensagens = query.order_by(MensagemChat.data_envio.desc()).limit(20).all()
    
    return jsonify([mensagem.to_dict() for mensagem in mensagens])

