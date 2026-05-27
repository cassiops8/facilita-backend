from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.funcionaria import Funcionaria
from src.models.cliente import Cliente
from src.models.log_auditoria import LogAuditoria
import json

funcionaria_bp = Blueprint("funcionaria", __name__)

@funcionaria_bp.route("/funcionarias", methods=["GET"])
@jwt_required()
def listar_funcionarias():
    """Lista todas as funcionárias"""
    try:
        current_user_id = get_jwt_identity()
        # Apenas administradores podem listar todas as funcionárias
        current_user = Funcionaria.query.get(current_user_id)
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
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)
        if not current_user or not current_user.is_admin:
            return jsonify({"error": "Acesso não autorizado"}), 403

        data = request.get_json()
        print(f"Dados recebidos no backend (criar_funcionaria): {data}")
        if Funcionaria.query.filter_by(email=data["email"]).first():
            return jsonify({"erro": "Email já cadastrado"}), 400

        funcionaria = Funcionaria(
            nome=data["nome"],
            email=data["email"],
            senha=generate_password_hash(data["senha"]),
            telefone=data.get("telefone"),
            is_admin=data.get("is_admin", False),
            ativa=data.get("ativa", True),
            categoria_id=data.get("categoria_id")
        )
        db.session.add(funcionaria)
        db.session.commit()
        return jsonify(funcionaria.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
