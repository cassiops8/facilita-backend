from src.models.user import db
from datetime import datetime

class TipoCliente(db.Model):
    __tablename__ = 'tipos_cliente'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    setor = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com clientes
    clientes = db.relationship('Cliente', backref='tipo_cliente_obj', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'setor': self.setor,
            'descricao': self.descricao,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }

