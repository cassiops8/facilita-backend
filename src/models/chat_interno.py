from src.models.user import db
from src.models.funcionaria import Funcionaria

class GrupoChat(db.Model):
    __tablename__ = 'grupos_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), default='grupo')  # 'grupo', 'direto', 'geral'
    privado = db.Column(db.Boolean, default=False)
    cor = db.Column(db.String(7), default='#8B4513')  # Cor do grupo em hex
    icone = db.Column(db.String(50), default='MessageCircle')  # Nome do ícone Lucide
    criado_por = db.Column(db.Integer, db.ForeignKey('funcionarias.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    criador = db.relationship('Funcionaria', backref=db.backref('grupos_criados', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'privado': self.privado,
            'cor': self.cor,
            'icone': self.icone,
            'criado_por': self.criado_por,
            'criador_nome': self.criador.nome if self.criador else None,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'ativo': self.ativo,
            'total_membros': len(self.membros) if hasattr(self, 'membros') else 0,
            'ultima_mensagem': self.get_ultima_mensagem()
        }
    
    def get_ultima_mensagem(self):
        ultima = MensagemChat.query.filter_by(grupo_id=self.id).order_by(MensagemChat.data_envio.desc()).first()
        if ultima:
            return {
                'id': ultima.id,
                'conteudo': ultima.conteudo[:50] + '...' if len(ultima.conteudo) > 50 else ultima.conteudo,
                'remetente_nome': ultima.remetente.nome if ultima.remetente else 'Sistema',
                'data_envio': ultima.data_envio.isoformat()
            }
        return None
    
    def __repr__(self):
        return f'<GrupoChat {self.nome}>'

class MembroGrupo(db.Model):
    __tablename__ = 'membros_grupo'
    
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_chat.id'), nullable=False)
    funcionaria_id = db.Column(db.Integer, db.ForeignKey('funcionarias.id'), nullable=False)
    papel = db.Column(db.String(20), default='membro')  # 'admin', 'moderador', 'membro'
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    notificacoes = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    grupo = db.relationship('GrupoChat', backref=db.backref('membros', lazy=True))
    funcionaria = db.relationship('Funcionaria', backref=db.backref('grupos_membro', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'grupo_id': self.grupo_id,
            'funcionaria_id': self.funcionaria_id,
            'funcionaria_nome': self.funcionaria.nome if self.funcionaria else None,
            'funcionaria_email': self.funcionaria.email if self.funcionaria else None,
            'papel': self.papel,
            'data_entrada': self.data_entrada.isoformat() if self.data_entrada else None,
            'ativo': self.ativo,
            'notificacoes': self.notificacoes
        }
    
    def __repr__(self):
        return f'<MembroGrupo {self.funcionaria.nome if self.funcionaria else "N/A"} - {self.grupo.nome if self.grupo else "N/A"}>'

class MensagemChat(db.Model):
    __tablename__ = 'mensagens_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_chat.id'), nullable=False)
    remetente_id = db.Column(db.Integer, db.ForeignKey('funcionarias.id'), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='texto')  # 'texto', 'arquivo', 'imagem', 'sistema'
    arquivo_url = db.Column(db.String(500), nullable=True)
    arquivo_nome = db.Column(db.String(255), nullable=True)
    resposta_para = db.Column(db.Integer, db.ForeignKey('mensagens_chat.id'), nullable=True)
    editada = db.Column(db.Boolean, default=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    data_edicao = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    grupo = db.relationship('GrupoChat', backref=db.backref('mensagens', lazy=True))
    remetente = db.relationship('Funcionaria', backref=db.backref('mensagens_enviadas', lazy=True))
    mensagem_original = db.relationship('MensagemChat', remote_side=[id], backref='respostas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'grupo_id': self.grupo_id,
            'remetente_id': self.remetente_id,
            'remetente_nome': self.remetente.nome if self.remetente else 'Sistema',
            'remetente_email': self.remetente.email if self.remetente else None,
            'conteudo': self.conteudo,
            'tipo': self.tipo,
            'arquivo_url': self.arquivo_url,
            'arquivo_nome': self.arquivo_nome,
            'resposta_para': self.resposta_para,
            'mensagem_original': self.mensagem_original.to_dict() if self.mensagem_original else None,
            'editada': self.editada,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'data_edicao': self.data_edicao.isoformat() if self.data_edicao else None
        }
    
    def __repr__(self):
        return f'<MensagemChat {self.id} - {self.remetente.nome if self.remetente else "Sistema"}>'

class StatusLeitura(db.Model):
    __tablename__ = 'status_leitura'
    
    id = db.Column(db.Integer, primary_key=True)
    mensagem_id = db.Column(db.Integer, db.ForeignKey('mensagens_chat.id'), nullable=False)
    funcionaria_id = db.Column(db.Integer, db.ForeignKey('funcionarias.id'), nullable=False)
    lida = db.Column(db.Boolean, default=False)
    data_leitura = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    mensagem = db.relationship('MensagemChat', backref=db.backref('status_leitura', lazy=True))
    funcionaria = db.relationship('Funcionaria', backref=db.backref('mensagens_lidas', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'mensagem_id': self.mensagem_id,
            'funcionaria_id': self.funcionaria_id,
            'funcionaria_nome': self.funcionaria.nome if self.funcionaria else None,
            'lida': self.lida,
            'data_leitura': self.data_leitura.isoformat() if self.data_leitura else None
        }
    
    def __repr__(self):
        return f'<StatusLeitura {self.funcionaria.nome if self.funcionaria else "N/A"} - Msg {self.mensagem_id}>'

