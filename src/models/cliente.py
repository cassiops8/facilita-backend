from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    tipo_profissional = db.Column(db.String(50), nullable=False)  # médico, esteticista, massoterapeuta, etc.
    tipo_cliente_id = db.Column(db.Integer, db.ForeignKey('tipos_cliente.id'), nullable=True)
    setor = db.Column(db.String(100), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Chave estrangeira para funcionária responsável
    funcionaria_id = db.Column(db.Integer, db.ForeignKey('funcionaria.id'), nullable=False)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='cliente', lazy=True)
    conversas = db.relationship('Conversa', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'telefone': self.telefone,
            'email': self.email,
            'tipo_profissional': self.tipo_profissional,
            'tipo_cliente_id': self.tipo_cliente_id,
            'setor': self.setor,
            'endereco': self.endereco,
            'observacoes': self.observacoes,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'funcionaria_id': self.funcionaria_id,
            'total_agendamentos': len(self.agendamentos),
            'conversas_ativas': len([c for c in self.conversas if c.ativa])
        }

