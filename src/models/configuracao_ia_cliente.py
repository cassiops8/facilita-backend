from src.models.user import db
from datetime import datetime

class ConfiguracaoIACliente(db.Model):
    __tablename__ = 'configuracao_ia_cliente'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Configurações básicas
    ativa = db.Column(db.Boolean, default=False)
    modelo_ia = db.Column(db.String(50), default='gpt-3.5-turbo')
    personalidade = db.Column(db.String(50), default='profissional')
    tom_comunicacao = db.Column(db.String(50), default='formal')
    
    # Base de conhecimento personalizada
    conhecimento_base = db.Column(db.Text)
    instrucoes_especiais = db.Column(db.Text)
    faq_personalizado = db.Column(db.Text)
    servicos_oferecidos = db.Column(db.Text)
    tabela_precos = db.Column(db.Text)
    
    # Configurações avançadas
    temperatura = db.Column(db.Float, default=0.7)  # Criatividade da IA
    max_tokens = db.Column(db.Integer, default=500)  # Tamanho máximo da resposta
    contexto_conversa = db.Column(db.Boolean, default=True)  # Manter contexto
    
    # Configurações de comportamento
    usar_emojis = db.Column(db.Boolean, default=False)
    mencionar_nome_cliente = db.Column(db.Boolean, default=True)
    solicitar_feedback = db.Column(db.Boolean, default=True)
    
    # Horários de funcionamento da IA
    horario_ia_inicio = db.Column(db.String(5), default='08:00')
    horario_ia_fim = db.Column(db.String(5), default='20:00')
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref='configuracao_ia')
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'ativa': self.ativa,
            'modelo_ia': self.modelo_ia,
            'personalidade': self.personalidade,
            'tom_comunicacao': self.tom_comunicacao,
            'conhecimento_base': self.conhecimento_base,
            'instrucoes_especiais': self.instrucoes_especiais,
            'faq_personalizado': self.faq_personalizado,
            'servicos_oferecidos': self.servicos_oferecidos,
            'tabela_precos': self.tabela_precos,
            'temperatura': self.temperatura,
            'max_tokens': self.max_tokens,
            'contexto_conversa': self.contexto_conversa,
            'usar_emojis': self.usar_emojis,
            'mencionar_nome_cliente': self.mencionar_nome_cliente,
            'solicitar_feedback': self.solicitar_feedback,
            'horario_ia_inicio': self.horario_ia_inicio,
            'horario_ia_fim': self.horario_ia_fim,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

