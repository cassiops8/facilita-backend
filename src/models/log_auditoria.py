from src.models.user import db
from datetime import datetime

class LogAuditoria(db.Model):
    __tablename__ = 'logs_auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('funcionaria.id'), nullable=False)
    acao = db.Column(db.String(100), nullable=False)  # CREATE, UPDATE, DELETE
    tabela = db.Column(db.String(100), nullable=False)  # Nome da tabela afetada
    registro_id = db.Column(db.Integer)  # ID do registro afetado
    dados_anteriores = db.Column(db.Text)  # JSON dos dados antes da alteração
    dados_novos = db.Column(db.Text)  # JSON dos dados após a alteração
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com funcionária
    usuario = db.relationship('Funcionaria', backref='logs_auditoria', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome if self.usuario else None,
            'acao': self.acao,
            'tabela': self.tabela,
            'registro_id': self.registro_id,
            'dados_anteriores': self.dados_anteriores,
            'dados_novos': self.dados_novos,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None
        }

