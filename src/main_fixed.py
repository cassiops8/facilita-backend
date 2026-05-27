import os
import sys
import traceback

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from flask import Flask, send_from_directory
    from flask_cors import CORS
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
    app.register_blueprint(categoria_colaborador_bp)
    app.register_blueprint(tipo_cliente_bp)
    app.register_blueprint(log_auditoria_bp)

    # Configuração do banco de dados
    database_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
            print("Banco de dados criado com sucesso!")
        except Exception as e:
            print(f"Erro ao criar banco de dados: {e}")
            traceback.print_exc()

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

    @app.errorhandler(500)
    def internal_error(error):
        print(f"Erro 500: {error}")
        traceback.print_exc()
        return {"error": "Erro interno do servidor"}, 500

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5001, debug=True)

except Exception as e:
    print(f"Erro crítico durante a inicialização: {e}")
    traceback.print_exc()

