import os
import sys
import traceback
from datetime import timedelta

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from flask import Flask, send_from_directory
    from flask_cors import CORS
    from flask_jwt_extended import JWTManager
    from dotenv import load_dotenv
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    from src.models.user import db
    from src.models.funcionaria import Funcionaria
    from src.models.cliente import Cliente
    from src.models.agendamento import Agendamento
    from src.models.conversa import Conversa, Mensagem
    from src.models.categoria_colaborador import CategoriaColaborador
    from src.models.tipo_cliente import TipoCliente
    from src.models.log_auditoria import LogAuditoria
    from src.models.configuracao_whatsapp_cliente import ConfiguracaoWhatsAppCliente
    from src.models.configuracao_ia_cliente import ConfiguracaoIACliente
    from src.routes.user import user_bp
    from src.routes.funcionaria import funcionaria_bp
    from src.routes.cliente import cliente_bp
    from src.routes.agendamento import agendamento_bp
    from src.routes.conversa import conversa_bp
    from src.routes.categoria_colaborador import categoria_colaborador_bp
    from src.routes.tipo_cliente import tipo_cliente_bp
    from src.routes.log_auditoria import log_auditoria_bp
    from src.routes.chat_interno import chat_interno_bp
    from src.routes.ia_config import ia_config_bp
    from src.routes.whatsapp_config import whatsapp_config_bp
    from src.routes.configuracao_sistema import configuracao_sistema_bp

    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configurações da aplicação
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'facilita-ar-secret-key-2024')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'facilita-ar-jwt-secret-key-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400)))

    # Habilitar CORS - permite frontend em produção e local
    CORS(app, resources={r"/api/*": {
        "origins": [
            "https://facilita-frontend-3.onrender.com",
            "http://localhost:5173",
            "http://localhost:3000"
        ],
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }})

    # Configurar JWT
    jwt = JWTManager(app)

    # Registrar blueprints
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(funcionaria_bp, url_prefix='/api')
    app.register_blueprint(cliente_bp, url_prefix='/api')
    app.register_blueprint(agendamento_bp, url_prefix='/api')
    app.register_blueprint(conversa_bp, url_prefix='/api')
    app.register_blueprint(categoria_colaborador_bp)
    app.register_blueprint(tipo_cliente_bp)
    app.register_blueprint(log_auditoria_bp)
    app.register_blueprint(chat_interno_bp, url_prefix='/api')
    app.register_blueprint(ia_config_bp, url_prefix='/api')
    app.register_blueprint(whatsapp_config_bp, url_prefix='/api')
    app.register_blueprint(configuracao_sistema_bp, url_prefix='/api')

    # Configuração do banco de dados
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        database_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
            print("Banco de dados criado com sucesso!")
            
            admin_email = 'cassiops7@gmail.com'
            admin_user = Funcionaria.query.filter_by(email=admin_email).first()
            if not admin_user:
                from werkzeug.security import generate_password_hash
                admin_user = Funcionaria(
                    nome='Administrador Principal',
                    email=admin_email,
                    senha=generate_password_hash('F1234567'),
                    telefone='(11) 99999-0000',
                    is_admin=True,
                    ativa=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("Usuário administrador criado com sucesso!")
                
        except Exception as e:
            print(f"Erro ao criar banco de dados: {e}")
            traceback.print_exc()

except Exception as e:
    print(f"Erro crítico durante a inicialização: {e}")
    traceback.print_exc()
    app = None

@app.route('/api/health')
def health_check():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    if app:
        port = int(os.getenv('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("Aplicação Flask não inicializada devido a erros.")
