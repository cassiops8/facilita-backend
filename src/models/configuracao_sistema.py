from src.models.user import db
from datetime import datetime
import json

class ConfiguracaoSistema(db.Model):
    __tablename__ = 'configuracoes_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), default='string')  # 'string', 'json', 'boolean', 'number', 'file'
    categoria = db.Column(db.String(50), default='geral')  # 'aparencia', 'whitelabel', 'sistema', 'integracao'
    descricao = db.Column(db.Text, nullable=True)
    editavel = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        valor_processado = self.valor
        
        # Processar valor baseado no tipo
        if self.tipo == 'json' and self.valor:
            try:
                valor_processado = json.loads(self.valor)
            except:
                valor_processado = {}
        elif self.tipo == 'boolean':
            valor_processado = self.valor.lower() == 'true' if self.valor else False
        elif self.tipo == 'number' and self.valor:
            try:
                valor_processado = float(self.valor)
            except:
                valor_processado = 0
        
        return {
            'id': self.id,
            'chave': self.chave,
            'valor': valor_processado,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'editavel': self.editavel,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def set_valor(self, valor):
        """Define o valor convertendo para string conforme o tipo"""
        if self.tipo == 'json':
            self.valor = json.dumps(valor) if valor else '{}'
        elif self.tipo == 'boolean':
            self.valor = 'true' if valor else 'false'
        else:
            self.valor = str(valor) if valor is not None else ''
    
    @staticmethod
    def obter_valor(chave, valor_padrao=None):
        """Obtém o valor de uma configuração"""
        config = ConfiguracaoSistema.query.filter_by(chave=chave).first()
        if not config:
            return valor_padrao
        
        if config.tipo == 'json':
            try:
                return json.loads(config.valor) if config.valor else {}
            except:
                return valor_padrao or {}
        elif config.tipo == 'boolean':
            return config.valor.lower() == 'true' if config.valor else False
        elif config.tipo == 'number':
            try:
                return float(config.valor) if config.valor else 0
            except:
                return valor_padrao or 0
        else:
            return config.valor or valor_padrao
    
    @staticmethod
    def definir_valor(chave, valor, tipo='string', categoria='geral', descricao=None):
        """Define ou atualiza uma configuração"""
        config = ConfiguracaoSistema.query.filter_by(chave=chave).first()
        
        if config:
            config.set_valor(valor)
            config.data_atualizacao = datetime.utcnow()
        else:
            config = ConfiguracaoSistema(
                chave=chave,
                tipo=tipo,
                categoria=categoria,
                descricao=descricao
            )
            config.set_valor(valor)
            db.session.add(config)
        
        db.session.commit()
        return config
    
    def __repr__(self):
        return f'<ConfiguracaoSistema {self.chave}: {self.valor}>'

class InstanciaWhitelabel(db.Model):
    __tablename__ = 'instancias_whitelabel'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    subdominio = db.Column(db.String(50), unique=True, nullable=False)
    logo_url = db.Column(db.String(500), nullable=True)
    cores_personalizadas = db.Column(db.Text, nullable=True)  # JSON com paleta de cores
    configuracoes_personalizadas = db.Column(db.Text, nullable=True)  # JSON com outras configs
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        cores = {}
        configs = {}
        
        if self.cores_personalizadas:
            try:
                cores = json.loads(self.cores_personalizadas)
            except:
                cores = {}
        
        if self.configuracoes_personalizadas:
            try:
                configs = json.loads(self.configuracoes_personalizadas)
            except:
                configs = {}
        
        return {
            'id': self.id,
            'nome': self.nome,
            'subdominio': self.subdominio,
            'logo_url': self.logo_url,
            'cores_personalizadas': cores,
            'configuracoes_personalizadas': configs,
            'ativa': self.ativa,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'url_completa': f"https://{self.subdominio}.facilita-ar.com" if self.subdominio else None
        }
    
    def set_cores(self, cores_dict):
        """Define as cores personalizadas"""
        self.cores_personalizadas = json.dumps(cores_dict) if cores_dict else '{}'
    
    def get_cores(self):
        """Obtém as cores personalizadas"""
        if self.cores_personalizadas:
            try:
                return json.loads(self.cores_personalizadas)
            except:
                return {}
        return {}
    
    def set_configuracoes(self, configs_dict):
        """Define as configurações personalizadas"""
        self.configuracoes_personalizadas = json.dumps(configs_dict) if configs_dict else '{}'
    
    def get_configuracoes(self):
        """Obtém as configurações personalizadas"""
        if self.configuracoes_personalizadas:
            try:
                return json.loads(self.configuracoes_personalizadas)
            except:
                return {}
        return {}
    
    def __repr__(self):
        return f'<InstanciaWhitelabel {self.nome} - {self.subdominio}>'

