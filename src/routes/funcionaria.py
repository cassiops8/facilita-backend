from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.funcionaria import Funcionaria
from src.models.cliente import Cliente
from src.models.log_auditoria import LogAuditoria
import json

funcionaria_bp = Blueprint("funcionaria", __name__)

def get_current_user():
    """Helper para pegar o usuário atual convertendo ID para int"""
    current_user_id = get_jwt_identity()
    try:
        user_id = int(current_user_id)
    except (TypeError, ValueError):
        return None
    return Funcionaria.query.get(user_id)

@funcionaria_bp.route("/funcionarias", methods=["GET"])
@jwt_required()
def listar_funcionarias():
    """Lista todas as funcionárias"""
    try:
        current_user = get_current_user()
        if not current_user or not current_user.is_admin:
            return jsonify({"error": "Acesso não autorizado"}), 403
        funcionarias = Funcionaria.query.all()
        return jsonify([f.to_dict() for f in funcionarias])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@funcionaria_bp.route("/funcionarias", methods=["POST"])
@jwt_required()
def criar_funcionaria():
    """Cria uma nova funcionária"""
    try:
        current_user = get_current_user()
        if not current_user or not current_user.is_admin:
            return jsonify({"error": "Acesso não autorizado"}), 403
        data = request.get_json()
        print(f"Dados recebidos no backend (criar_funcionaria): {data}")
        if Funcionaria.query.filter_by(email=data["email"]).first():
            return jsonify({"erro": "Email já cadastrado"}), 400
        
        # Tratar categoria_id - converter para int ou None
        categoria_id = data.get("categoria_id")
        if categoria_id == '' or categoria_id is None:
            categoria_id = None
        else:
            try:
                categoria_id = int(categoria_id)
            except (TypeError, ValueError):
                categoria_id = None
        
        funcionaria = Funcionaria(
            nome=data["nome"],
            email=data["email"],
            senha=generate_password_hash(data["senha"]),
            telefone=data.get("telefone"),
            is_admin=data.get("is_admin", False),
            ativa=data.get("ativa", True),
            categoria_id=categoria_id
        )
        db.session.add(funcionaria)
        db.session.commit()
        return jsonify(funcionaria.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@funcionaria_bp.route("/funcionarias/me", methods=["GET"])
@jwt_required()
def get_me():
    """Retorna dados do usuário logado"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        return jsonify(current_user.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@funcionaria_bp.route("/funcionarias/<int:funcionaria_id>", methods=["GET"])
@jwt_required()
def get_funcionaria(funcionaria_id):
    """Retorna dados de uma funcionária específica"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "Não autorizado"}), 401
        funcionaria = Funcionaria.query.get(funcionaria_id)
        if not funcionaria:
            return jsonify({"error": "Funcionária não encontrada"}), 404
        return jsonify(funcionaria.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@funcionaria_bp.route("/funcionarias/<int:funcionaria_id>", methods=["PUT"])
@jwt_required()
def atualizar_funcionaria(funcionaria_id):
    """Atualiza uma funcionária"""
    try:
        current_user = get_current_user()
        if not current_user or not current_user.is_admin:
            return jsonify({"error": "Acesso não autorizado"}), 403
        funcionaria = Funcionaria.query.get(funcionaria_id)
        if not funcionaria:
            return jsonify({"error": "Funcionária não encontrada"}), 404
        data = request.get_json()
        for key, value in data.items():
            if key == 'senha' and value:
                setattr(funcionaria, key, generate_password_hash(value))
            elif hasattr(funcionaria, key):
                setattr(funcionaria, key, value)
        db.session.commit()
        return jsonify(funcionaria.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@funcionaria_bp.route("/recuperar-senha", methods=["POST"])
def recuperar_senha():
    """Inicia o processo de recuperação de senha"""
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return jsonify({"erro": "Email é obrigatório"}), 400
        funcionaria = Funcionaria.query.filter_by(email=email).first()
        if funcionaria:
            return jsonify({"mensagem": "Se o email existir, instruções foram enviadas."}), 200
        return jsonify({"mensagem": "Se o email existir, instruções foram enviadas."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
