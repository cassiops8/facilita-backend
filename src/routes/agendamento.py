from flask import Blueprint, request, jsonify
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.agendamento import Agendamento
from src.models.cliente import Cliente
from src.models.funcionaria import Funcionaria
from src.models.log_auditoria import LogAuditoria
import json

agendamento_bp = Blueprint("agendamento", __name__)

@agendamento_bp.route("/agendamentos", methods=["GET"])
@jwt_required()
def listar_agendamentos():
    """Lista todos os agendamentos"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        cliente_id = request.args.get("cliente_id")
        funcionaria_id = request.args.get("funcionaria_id")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")

        query = Agendamento.query

        if cliente_id:
            cliente = Cliente.query.get(cliente_id)
            if not cliente:
                return jsonify({"error": "Cliente não encontrado"}), 404
            # Usuário só pode ver agendamentos de seus próprios clientes ou se for admin
            if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
                return jsonify({"error": "Acesso não autorizado"}), 403
            query = query.filter_by(cliente_id=cliente_id)

        if funcionaria_id:
            # Apenas administradores podem listar agendamentos de outras funcionárias
            if not current_user.is_admin and str(current_user_id) != funcionaria_id:
                return jsonify({"error": "Acesso não autorizado"}), 403
            # Filtrar por funcionária através do cliente
            clientes_funcionaria = Cliente.query.filter_by(funcionaria_id=funcionaria_id).all()
            cliente_ids = [c.id for c in clientes_funcionaria]
            query = query.filter(Agendamento.cliente_id.in_(cliente_ids))
        else:
            # Se não for admin, só pode ver seus próprios agendamentos
            if not current_user.is_admin:
                clientes_funcionaria = Cliente.query.filter_by(funcionaria_id=current_user_id).all()
                cliente_ids = [c.id for c in clientes_funcionaria]
                query = query.filter(Agendamento.cliente_id.in_(cliente_ids))

        if data_inicio:
            data_inicio_dt = datetime.fromisoformat(data_inicio)
            query = query.filter(Agendamento.data_hora >= data_inicio_dt)

        if data_fim:
            data_fim_dt = datetime.fromisoformat(data_fim)
            query = query.filter(Agendamento.data_hora <= data_fim_dt)

        agendamentos = query.order_by(Agendamento.data_hora.asc()).all()
        return jsonify([a.to_dict() for a in agendamentos])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agendamento_bp.route("/agendamentos", methods=["POST"])
@jwt_required()
def criar_agendamento():
    """Cria um novo agendamento"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        data = request.get_json()

        cliente = Cliente.query.get(data["cliente_id"])
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        # Usuário só pode criar agendamento para seus próprios clientes ou se for admin
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        agendamento = Agendamento(
            titulo=data["titulo"],
            descricao=data.get("descricao"),
            data_hora=datetime.fromisoformat(data["data_hora"]),
            duracao_minutos=data.get("duracao_minutos", 60),
            tipo=data["tipo"],
            local=data.get("local"),
            observacoes=data.get("observacoes"),
            cliente_id=data["cliente_id"],
            nome_paciente=data["nome_paciente"],
            telefone_paciente=data.get("telefone_paciente"),
            email_paciente=data.get("email_paciente"),
        )

        db.session.add(agendamento)
        db.session.commit()

        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=current_user.nome,
                acao='CREATE',
                tabela='agendamento',
                registro_id=agendamento.id,
                dados_novos=json.dumps(agendamento.to_dict()),
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar

        return jsonify(agendamento.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@agendamento_bp.route("/agendamentos/<int:agendamento_id>", methods=["GET"])
@jwt_required()
def obter_agendamento(agendamento_id):
    """Obtém um agendamento específico"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        agendamento = Agendamento.query.get_or_404(agendamento_id)

        # Usuário só pode ver agendamentos de seus próprios clientes ou se for admin
        cliente = Cliente.query.get(agendamento.cliente_id)
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        return jsonify(agendamento.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agendamento_bp.route("/agendamentos/<int:agendamento_id>", methods=["PUT"])
@jwt_required()
def atualizar_agendamento(agendamento_id):
    """Atualiza um agendamento"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        agendamento = Agendamento.query.get_or_404(agendamento_id)

        # Usuário só pode atualizar agendamentos de seus próprios clientes ou se for admin
        cliente = Cliente.query.get(agendamento.cliente_id)
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        data = request.get_json()
        dados_anteriores = agendamento.to_dict()

        agendamento.titulo = data.get("titulo", agendamento.titulo)
        agendamento.descricao = data.get("descricao", agendamento.descricao)
        agendamento.duracao_minutos = data.get("duracao_minutos", agendamento.duracao_minutos)
        agendamento.status = data.get("status", agendamento.status)
        agendamento.tipo = data.get("tipo", agendamento.tipo)
        agendamento.local = data.get("local", agendamento.local)
        agendamento.observacoes = data.get("observacoes", agendamento.observacoes)
        agendamento.nome_paciente = data.get("nome_paciente", agendamento.nome_paciente)
        agendamento.telefone_paciente = data.get("telefone_paciente", agendamento.telefone_paciente)
        agendamento.email_paciente = data.get("email_paciente", agendamento.email_paciente)

        if "data_hora" in data:
            agendamento.data_hora = datetime.fromisoformat(data["data_hora"])

        agendamento.data_atualizacao = datetime.utcnow()

        db.session.commit()

        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=current_user.nome,
                acao='UPDATE',
                tabela='agendamento',
                registro_id=agendamento.id,
                dados_anteriores=json.dumps(dados_anteriores),
                dados_novos=json.dumps(agendamento.to_dict()),
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar

        return jsonify(agendamento.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@agendamento_bp.route("/agendamentos/<int:agendamento_id>", methods=["DELETE"])
@jwt_required()
def deletar_agendamento(agendamento_id):
    """Deleta um agendamento"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        agendamento = Agendamento.query.get_or_404(agendamento_id)

        # Usuário só pode deletar agendamentos de seus próprios clientes ou se for admin
        cliente = Cliente.query.get(agendamento.cliente_id)
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        dados_anteriores = agendamento.to_dict()

        db.session.delete(agendamento)
        db.session.commit()

        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=current_user.nome,
                acao='DELETE',
                tabela='agendamento',
                registro_id=agendamento_id,
                dados_anteriores=json.dumps(dados_anteriores),
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar

        return "", 204

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@agendamento_bp.route("/agendamentos/<int:agendamento_id>/status", methods=["PUT"])
@jwt_required()
def atualizar_status_agendamento(agendamento_id):
    """Atualiza apenas o status de um agendamento"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        agendamento = Agendamento.query.get_or_404(agendamento_id)

        # Usuário só pode atualizar agendamentos de seus próprios clientes ou se for admin
        cliente = Cliente.query.get(agendamento.cliente_id)
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        data = request.get_json()
        dados_anteriores = agendamento.to_dict()

        agendamento.status = data["status"]
        agendamento.data_atualizacao = datetime.utcnow()

        db.session.commit()

        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=current_user.nome,
                acao='UPDATE',
                tabela='agendamento',
                registro_id=agendamento.id,
                dados_anteriores=json.dumps(dados_anteriores),
                dados_novos=json.dumps(agendamento.to_dict()),
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar

        return jsonify(agendamento.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
