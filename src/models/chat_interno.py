from src.models.user import db
from datetime import datetime

class GrupoChat(db.Model):
    __tablename__ = 'grupos_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), default='grupo')
    privado = db.Column(db.Boolean, default=False)
    cor = db.Column(db.String(7), default='#8B4513')
    icone = db.Column(db.String(50), default='MessageCircle')
    criado_por = db.Column(db.Integer, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
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
                'data_envio': ultima.data_envio.isoformat()
            }
        return None

class MembroGrupo(db.Model):
    __tablename__ = 'membros_grupo'
    
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_chat.id'), nullable=False)
    funcionaria_id = db.Column(db.Integer, nullable=True)
    papel = db.Column(db.String(20), default='membro')
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    notificacoes = db.Column(db.Boolean, default=True)
    
    grupo = db.relationship('GrupoChat', backref=db.backref('membros', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'grupo_id': self.grupo_id,
            'funcionaria_id': self.funcionaria_id,
            'papel': self.papel,
            'data_entrada': self.data_entrada.isoformat() if self.data_entrada else None,
            'ativo': self.ativo,
            'notificacoes': self.notificacoes
        }

class MensagemChat(db.Model):
    __tablename__ = 'mensagens_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_chat.id'), nullable=False)
    remetente_id = db.Column(db.Integer, nullable=True)
    conteudo = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='texto')
    arquivo_url = db.Column(db.String(500), nullable=True)
    arquivo_nome = db.Column(db.String(255), nullable=True)
    resposta_para = db.Column(db.Integer, db.ForeignKey('mensagens_chat.id'), nullable=True)
    editada = db.Column(db.Boolean, default=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    data_edicao = db.Column(db.DateTime, nullable=True)
    
    grupo = db.relationship('GrupoChat', backref=db.backref('mensagens', lazy=True))
    mensagem_original = db.relationship('MensagemChat', remote_side=[id], backref='respostas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'grupo_id': self.grupo_id,
            'remetente_id': self.remetente_id,
            'conteudo': self.conteudo,
            'tipo': self.tipo,
            'arquivo_url': self.arquivo_url,
            'arquivo_nome': self.arquivo_nome,
            'resposta_para': self.resposta_para,
            'editada': self.editada,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'data_edicao': self.data_edicao.isoformat() if self.data_edicao else None
        }

class StatusLeitura(db.Model):
    __tablename__ = 'status_leitura'
    
    id = db.Column(db.Integer, primary_key=True)
    mensagem_id = db.Column(db.Integer, db.ForeignKey('mensagens_chat.id'), nullable=False)
    funcionaria_id = db.Column(db.Integer, nullable=True)
    lida = db.Column(db.Boolean, default=False)
    data_leitura = db.Column(db.DateTime, nullable=True)
    
    mensagem = db.relationship('MensagemChat', backref=db.backref('status_leitura', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'mensagem_id': self.mensagem_id,
            'funcionaria_id': self.funcionaria_id,
            'lida': self.lida,
            'data_leitura': self.data_leitura.isoformat() if self.data_leitura else None
        }
