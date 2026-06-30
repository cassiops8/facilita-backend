from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from src.models.user import db
from src.models.funcionaria import Funcionaria
from src.models.log_auditoria import LogAuditoria
import json

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    """Login de funcionária com JWT"""
    try:
        data = request.get_json()
        print(f"Dados recebidos no login: {data}") # Adicionado para depuração
        email = data.get('email')
        senha = data.get('senha')
        
        if not email or not senha:
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        # Buscar funcionária
        funcionaria = Funcionaria.query.filter_by(email=email).first()
        
        if not funcionaria:
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        if not funcionaria.ativa:
            return jsonify({'error': 'Conta desativada'}), 401
        
        # Verificar senha
        if not check_password_hash(funcionaria.senha, senha):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Criar token JWT
        access_token = create_access_token(identity=str(funcionaria.id))
        
        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=funcionaria.id,
                usuario_nome=funcionaria.nome,
                acao='LOGIN',
                tabela='funcionaria',
                registro_id=funcionaria.id,
                dados_novos=json.dumps({'login_time': 'now'})
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar
        
        return jsonify({
            'access_token': access_token,
            'funcionaria': funcionaria.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obter dados do usuário atual"""
    try:
        current_user_id = get_jwt_identity()
        funcionaria = Funcionaria.query.get(current_user_id)
        
        if not funcionaria:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if not funcionaria.ativa:
            return jsonify({'error': 'Conta desativada'}), 401
        
        return jsonify(funcionaria.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout do usuário"""
    try:
        current_user_id = get_jwt_identity()
        funcionaria = Funcionaria.query.get(current_user_id)
        
        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=funcionaria.nome if funcionaria else 'Usuário desconhecido',
                acao='LOGOUT',
                tabela='funcionaria',
                registro_id=current_user_id,
                dados_novos=json.dumps({'logout_time': 'now'})
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar
        
        return jsonify({'message': 'Logout realizado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Alterar senha do usuário"""
    try:
        current_user_id = get_jwt_identity()
        funcionaria = Funcionaria.query.get(current_user_id)
        
        if not funcionaria:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        senha_atual = data.get('senha_atual')
        nova_senha = data.get('nova_senha')

        if not nova_senha:
            return jsonify({'error': 'A nova senha é obrigatória'}), 400

        # Se NÃO for senha temporária, exige a senha atual correta.
        # Se for primeiro acesso (senha_temporaria=True), não precisa da senha atual.
        if not funcionaria.senha_temporaria:
            if not senha_atual:
                return jsonify({'error': 'A senha atual é obrigatória'}), 400
            if not check_password_hash(funcionaria.senha, senha_atual):
                return jsonify({'error': 'Senha atual incorreta'}), 401

        # Atualizar senha e marcar como definitiva
        funcionaria.senha = generate_password_hash(nova_senha)
        funcionaria.senha_temporaria = False
        db.session.commit()
        
        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=funcionaria.nome,
                acao='UPDATE',
                tabela='funcionaria',
                registro_id=current_user_id,
                dados_novos=json.dumps({'password_changed': True})
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar
        
        return jsonify({'message': 'Senha alterada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
