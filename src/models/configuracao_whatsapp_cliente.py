from src.models.user import db
from datetime import datetime

class ConfiguracaoWhatsAppCliente(db.Model):
    __tablename__ = 'configuracao_whatsapp_cliente'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Configurações básicas
    ativo = db.Column(db.Boolean, default=False)
    numero_whatsapp = db.Column(db.String(20))
    token_acesso = db.Column(db.String(500))
    webhook_url = db.Column(db.String(500))
    
    # Mensagens personalizadas
    mensagem_boas_vindas = db.Column(db.Text)
    mensagem_ausencia = db.Column(db.Text)
    
    # Horários de atendimento
    horario_inicio = db.Column(db.String(5), default='09:00')
    horario_fim = db.Column(db.String(5), default='18:00')
    
    # Configurações avançadas
    resposta_automatica = db.Column(db.Boolean, default=True)
    notificacoes_ativas = db.Column(db.Boolean, default=True)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref='configuracao_whatsapp')
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'ativo': self.ativo,
            'numero_whatsapp': self.numero_whatsapp,
            'token_acesso': self.token_acesso,
            'webhook_url': self.webhook_url,
            'mensagem_boas_vindas': self.mensagem_boas_vindas,
            'mensagem_ausencia': self.mensagem_ausencia,
            'horario_inicio': self.horario_inicio,
            'horario_fim': self.horario_fim,
            'resposta_automatica': self.resposta_automatica,
            'notificacoes_ativas': self.notificacoes_ativas,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

