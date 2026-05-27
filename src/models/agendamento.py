from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_hora = db.Column(db.DateTime, nullable=False)
    duracao_minutos = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='agendado')  # agendado, confirmado, cancelado, realizado
    tipo = db.Column(db.String(50), nullable=False)  # consulta, reunião, procedimento, etc.
    local = db.Column(db.String(200), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Chave estrangeira para cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Dados do paciente/cliente final (quem será atendido)
    nome_paciente = db.Column(db.String(100), nullable=False)
    telefone_paciente = db.Column(db.String(20), nullable=True)
    email_paciente = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<Agendamento {self.titulo} - {self.data_hora}>'

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None,
            'duracao_minutos': self.duracao_minutos,
            'status': self.status,
            'tipo': self.tipo,
            'local': self.local,
            'observacoes': self.observacoes,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'cliente_id': self.cliente_id,
            'nome_paciente': self.nome_paciente,
            'telefone_paciente': self.telefone_paciente,
            'email_paciente': self.email_paciente
        }

