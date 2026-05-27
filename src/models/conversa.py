from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Conversa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_whatsapp = db.Column(db.String(20), nullable=False)
    nome_contato = db.Column(db.String(100), nullable=False)
    ativa = db.Column(db.Boolean, default=True)
    modo_ia = db.Column(db.Boolean, default=True)  # True = IA responde, False = funcionária responde
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atividade = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Chave estrangeira para cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Relacionamento com mensagens
    mensagens = db.relationship('Mensagem', backref='conversa', lazy=True, order_by='Mensagem.data_envio')

    def __repr__(self):
        return f'<Conversa {self.numero_whatsapp} - {self.nome_contato}>'

    def to_dict(self):
        return {
            'id': self.id,
            'numero_whatsapp': self.numero_whatsapp,
            'nome_contato': self.nome_contato,
            'ativa': self.ativa,
            'modo_ia': self.modo_ia,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'ultima_atividade': self.ultima_atividade.isoformat() if self.ultima_atividade else None,
            'cliente_id': self.cliente_id,
            'total_mensagens': len(self.mensagens),
            'ultima_mensagem': self.mensagens[-1].to_dict() if self.mensagens else None
        }

class Mensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='texto')  # texto, imagem, audio, documento
    remetente = db.Column(db.String(20), nullable=False)  # 'cliente', 'ia', 'funcionaria'
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)
    
    # Chave estrangeira para conversa
    conversa_id = db.Column(db.Integer, db.ForeignKey('conversa.id'), nullable=False)
    
    # ID da funcionária se foi ela quem enviou
    funcionaria_id = db.Column(db.Integer, db.ForeignKey('funcionaria.id'), nullable=True)

    def __repr__(self):
        return f'<Mensagem {self.remetente} - {self.data_envio}>'

    def to_dict(self):
        return {
            'id': self.id,
            'conteudo': self.conteudo,
            'tipo': self.tipo,
            'remetente': self.remetente,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'lida': self.lida,
            'conversa_id': self.conversa_id,
            'funcionaria_id': self.funcionaria_id
        }

