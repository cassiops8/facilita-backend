import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.funcionaria import Funcionaria
from src.models.cliente import Cliente
from src.models.agendamento import Agendamento
from src.models.conversa import Conversa, Mensagem
from src.models.whatsapp_config import WhatsAppConfig
from src.models.chat_interno import GrupoChat, MembroGrupo, MensagemChat, StatusLeitura
from src.models.configuracao_sistema import ConfiguracaoSistema, InstanciaWhitelabel
from src.routes.user import user_bp
from src.routes.funcionaria import funcionaria_bp
from src.routes.cliente import cliente_bp
from src.routes.agendamento import agendamento_bp
from src.routes.conversa import conversa_bp
from src.routes.whatsapp_config import whatsapp_config_bp
from src.routes.chat_interno import chat_interno_bp
from src.routes.configuracao_sistema import configuracao_sistema_bp
from src.routes.ia_config import ia_config_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'facilita-ar-secret-key-2024'

# Habilitar CORS para todas as rotas
CORS(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(funcionaria_bp, url_prefix='/api')
app.register_blueprint(cliente_bp, url_prefix='/api')
app.register_blueprint(agendamento_bp, url_prefix='/api')
app.register_blueprint(conversa_bp, url_prefix='/api')
app.register_blueprint(whatsapp_config_bp, url_prefix='/api')
app.register_blueprint(chat_interno_bp, url_prefix='/api')
app.register_blueprint(configuracao_sistema_bp, url_prefix='/api')
app.register_blueprint(ia_config_bp, url_prefix='/api')

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
