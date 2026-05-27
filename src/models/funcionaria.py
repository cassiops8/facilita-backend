from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db
from werkzeug.security import generate_password_hash, check_password_hash

class Funcionaria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    ativa = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_colaborador.id'), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime, nullable=True)
    
    # Relacionamento com clientes
    clientes = db.relationship('Cliente', backref='funcionaria_responsavel', lazy=True)

    def __repr__(self):
        return f'<Funcionaria {self.nome}>'
    
    def set_senha(self, senha):
        self.senha = generate_password_hash(senha)
    
    def check_senha(self, senha):
        return check_password_hash(self.senha, senha)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'ativa': self.ativa,
            'is_admin': self.is_admin,
            'categoria_id': self.categoria_id,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None,
            'total_clientes': len(self.clientes)
        }

