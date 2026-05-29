from src.models.user import db
from datetime import datetime

class WhatsAppConfig(db.Model):
    __tablename__ = 'whatsapp_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    numero_whatsapp = db.Column(db.String(20), nullable=False)
    nome_exibicao = db.Column(db.String(100), nullable=False)
    token_acesso = db.Column(db.String(500), nullable=True)
    phone_number_id = db.Column(db.String(100), nullable=True)
    webhook_verify_token = db.Column(db.String(100), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'numero_whatsapp': self.numero_whatsapp,
            'nome_exibicao': self.nome_exibicao,
            'token_acesso': self.token_acesso[:10] + '...' if self.token_acesso else None,  # Mascarar token
            'phone_number_id': self.phone_number_id,
            'webhook_verify_token': self.webhook_verify_token,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }
    
    def __repr__(self):
        return f'<WhatsAppConfig {self.numero_whatsapp} - {self.nome_exibicao}>'
