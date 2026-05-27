from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.cliente import Cliente
from src.models.agendamento import Agendamento
from src.models.conversa import Conversa
from src.models.configuracao_whatsapp_cliente import ConfiguracaoWhatsAppCliente
from src.models.configuracao_ia_cliente import ConfiguracaoIACliente
from src.models.log_auditoria import LogAuditoria
from src.models.funcionaria import Funcionaria
import json

cliente_bp = Blueprint("cliente", __name__)

@cliente_bp.route("/clientes", methods=["GET"])
@jwt_required()
def listar_clientes():
    """Lista todos os clientes"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        funcionaria_id = request.args.get("funcionaria_id")

        if funcionaria_id:
            # Apenas administradores podem listar clientes de outras funcionárias
            if not current_user.is_admin and str(current_user_id) != funcionaria_id:
                return jsonify({"error": "Acesso não autorizado"}), 403
            clientes = Cliente.query.filter_by(funcionaria_id=funcionaria_id).all()
        else:
            # Se não for admin, só pode ver seus próprios clientes
            if not current_user.is_admin:
                clientes = Cliente.query.filter_by(funcionaria_id=current_user_id).all()
            else:
                clientes = Cliente.query.all()
        return jsonify([c.to_dict() for c in clientes])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cliente_bp.route("/clientes", methods=["POST"])
@jwt_required()
def criar_cliente():
    """Cria um novo cliente com configurações de WhatsApp e IA"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        data = request.get_json()

        # Apenas admin pode criar clientes para outras funcionárias
        if "funcionaria_id" in data and str(data["funcionaria_id"]) != str(current_user_id) and not current_user.is_admin:
            return jsonify({"error": "Acesso não autorizado"}), 403

        # Se não for admin e não especificou funcionaria_id, atribui ao próprio usuário
        if not current_user.is_admin and "funcionaria_id" not in data:
            data["funcionaria_id"] = current_user_id

        # Criar cliente
        cliente = Cliente(
            nome=data["nome"],
            telefone=data["telefone"],
            email=data.get("email"),
            tipo_profissional=data["tipo_profissional"],
            tipo_cliente_id=data.get("tipo_cliente_id"),
            setor=data.get("setor"),
            endereco=data.get("endereco"),
            observacoes=data.get("observacoes"),
            funcionaria_id=data["funcionaria_id"],
        )

        db.session.add(cliente)
        db.session.flush()  # Para obter o ID do cliente

        # Configurar WhatsApp se fornecido
        if data.get("whatsapp_ativo"):
            config_whatsapp = ConfiguracaoWhatsAppCliente(
                cliente_id=cliente.id,
                ativo=data.get("whatsapp_ativo", False),
                numero_whatsapp=data.get("whatsapp_numero"),
                token_acesso=data.get("whatsapp_token"),
                webhook_url=data.get("whatsapp_webhook"),
                mensagem_boas_vindas=data.get("mensagem_boas_vindas"),
                mensagem_ausencia=data.get("mensagem_ausencia"),
                horario_inicio=data.get("horario_inicio", "09:00"),
                horario_fim=data.get("horario_fim", "18:00"),
            )
            db.session.add(config_whatsapp)

        # Configurar IA se fornecido
        if data.get("ia_ativa"):
            config_ia = ConfiguracaoIACliente(
                cliente_id=cliente.id,
                ativa=data.get("ia_ativa", False),
                modelo_ia=data.get("ia_modelo", "gpt-3.5-turbo"),
                personalidade=data.get("ia_personalidade", "profissional"),
                tom_comunicacao=data.get("ia_tom", "formal"),
                conhecimento_base=data.get("ia_conhecimento_base"),
                instrucoes_especiais=data.get("ia_instrucoes_especiais"),
                faq_personalizado=data.get("ia_faq"),
                servicos_oferecidos=data.get("ia_servicos"),
                tabela_precos=data.get("ia_precos"),
            )
            db.session.add(config_ia)

        db.session.commit()

        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=current_user.nome,
                acao='CREATE',
                tabela='cliente',
                registro_id=cliente.id,
                dados_novos=json.dumps(cliente.to_dict()),
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar

        return jsonify(cliente.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cliente_bp.route("/clientes/<int:cliente_id>", methods=["GET"])
@jwt_required()
def obter_cliente(cliente_id):
    """Obtém um cliente específico com suas configurações"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        cliente = Cliente.query.get_or_404(cliente_id)

        # Usuário só pode ver seus próprios clientes ou se for admin
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        cliente_dict = cliente.to_dict()

        # Incluir configurações de WhatsApp
        config_whatsapp = ConfiguracaoWhatsAppCliente.query.filter_by(
            cliente_id=cliente_id
        ).first()
        if config_whatsapp:
            cliente_dict["configuracao_whatsapp"] = config_whatsapp.to_dict()

        # Incluir configurações de IA
        config_ia = ConfiguracaoIACliente.query.filter_by(
            cliente_id=cliente_id
        ).first()
        if config_ia:
            cliente_dict["configuracao_ia"] = config_ia.to_dict()

        return jsonify(cliente_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cliente_bp.route("/clientes/<int:cliente_id>", methods=["PUT"])
@jwt_required()
def atualizar_cliente(cliente_id):
    """Atualiza um cliente e suas configurações"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        cliente = Cliente.query.get_or_404(cliente_id)

        # Usuário só pode atualizar seus próprios clientes ou se for admin
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        data = request.get_json()

        # Dados anteriores para log
        dados_anteriores = cliente.to_dict()

        # Atualizar dados básicos do cliente
        cliente.nome = data.get("nome", cliente.nome)
        cliente.telefone = data.get("telefone", cliente.telefone)
        cliente.email = data.get("email", cliente.email)
        cliente.tipo_profissional = data.get("tipo_profissional", cliente.tipo_profissional)
        cliente.tipo_cliente_id = data.get("tipo_cliente_id", cliente.tipo_cliente_id)
        cliente.setor = data.get("setor", cliente.setor)
        cliente.endereco = data.get("endereco", cliente.endereco)
        cliente.observacoes = data.get("observacoes", cliente.observacoes)
        cliente.ativo = data.get("ativo", cliente.ativo)

        # Apenas admin pode alterar a funcionaria_id
        if current_user.is_admin and "funcionaria_id" in data:
            cliente.funcionaria_id = data.get("funcionaria_id", cliente.funcionaria_id)

        # Atualizar configurações de WhatsApp
        config_whatsapp = ConfiguracaoWhatsAppCliente.query.filter_by(
            cliente_id=cliente_id
        ).first()
        if data.get("whatsapp_ativo"):
            if not config_whatsapp:
                config_whatsapp = ConfiguracaoWhatsAppCliente(cliente_id=cliente.id)
                db.session.add(config_whatsapp)

            config_whatsapp.ativo = data.get("whatsapp_ativo", False)
            config_whatsapp.numero_whatsapp = data.get("whatsapp_numero")
            config_whatsapp.token_acesso = data.get("whatsapp_token")
            config_whatsapp.webhook_url = data.get("whatsapp_webhook")
            config_whatsapp.mensagem_boas_vindas = data.get("mensagem_boas_vindas")
            config_whatsapp.mensagem_ausencia = data.get("mensagem_ausencia")
            config_whatsapp.horario_inicio = data.get("horario_inicio", "09:00")
            config_whatsapp.horario_fim = data.get("horario_fim", "18:00")
        elif config_whatsapp:
            config_whatsapp.ativo = False

        # Atualizar configurações de IA
        config_ia = ConfiguracaoIACliente.query.filter_by(
            cliente_id=cliente_id
        ).first()
        if data.get("ia_ativa"):
            if not config_ia:
                config_ia = ConfiguracaoIACliente(cliente_id=cliente.id)
                db.session.add(config_ia)

            config_ia.ativa = data.get("ia_ativa", False)
            config_ia.modelo_ia = data.get("ia_modelo", "gpt-3.5-turbo")
            config_ia.personalidade = data.get("ia_personalidade", "profissional")
            config_ia.tom_comunicacao = data.get("ia_tom", "formal")
            config_ia.conhecimento_base = data.get("ia_conhecimento_base")
            config_ia.instrucoes_especiais = data.get("ia_instrucoes_especiais")
            config_ia.faq_personalizado = data.get("ia_faq")
            config_ia.servicos_oferecidos = data.get("ia_servicos")
            config_ia.tabela_precos = data.get("ia_precos")
        elif config_ia:
            config_ia.ativo = False

        db.session.commit()

        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=current_user.nome,
                acao='UPDATE',
                tabela='cliente',
                registro_id=cliente.id,
                dados_anteriores=json.dumps(dados_anteriores),
                dados_novos=json.dumps(cliente.to_dict()),
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar

        return jsonify(cliente.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cliente_bp.route("/clientes/<int:cliente_id>", methods=["DELETE"])
@jwt_required()
def deletar_cliente(cliente_id):
    """Deleta um cliente e suas configurações"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        cliente = Cliente.query.get_or_404(cliente_id)

        # Usuário só pode deletar seus próprios clientes ou se for admin
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        dados_anteriores = cliente.to_dict()

        # Deletar configurações relacionadas
        ConfiguracaoWhatsAppCliente.query.filter_by(cliente_id=cliente_id).delete()
        ConfiguracaoIACliente.query.filter_by(cliente_id=cliente_id).delete()

        db.session.delete(cliente)
        db.session.commit()

        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=current_user.nome,
                acao='DELETE',
                tabela='cliente',
                registro_id=cliente_id,
                dados_anteriores=json.dumps(dados_anteriores),
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar

        return '', 204

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cliente_bp.route("/clientes/<int:cliente_id>/transferir", methods=["POST"])
@jwt_required()
def transferir_cliente(cliente_id):
    """Transfere um cliente para outra funcionária"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        # Apenas administradores podem transferir clientes
        if not current_user.is_admin:
            return jsonify({"error": "Acesso não autorizado"}), 403

        cliente = Cliente.query.get_or_404(cliente_id)
        data = request.get_json()
        nova_funcionaria_id = data.get("funcionaria_id")

        if not nova_funcionaria_id:
            return jsonify({"error": "funcionaria_id é obrigatório"}), 400

        funcionaria_anterior = cliente.funcionaria_id
        cliente.funcionaria_id = nova_funcionaria_id

        db.session.commit()

        # Log de auditoria
        try:
            log = LogAuditoria(
                usuario_id=current_user_id,
                usuario_nome=current_user.nome,
                acao='UPDATE',
                tabela='cliente',
                registro_id=cliente.id,
                dados_anteriores=json.dumps({"funcionaria_id": funcionaria_anterior}),
                dados_novos=json.dumps({"funcionaria_id": nova_funcionaria_id}),
            )
            db.session.add(log)
            db.session.commit()
        except:
            pass  # Não falhar se o log não funcionar

        return jsonify({"message": "Cliente transferido com sucesso", "cliente": cliente.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cliente_bp.route("/clientes/<int:cliente_id>/agendamentos", methods=["GET"])
@jwt_required()
def listar_agendamentos_cliente(cliente_id):
    """Lista todos os agendamentos de um cliente"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        cliente = Cliente.query.get_or_404(cliente_id)

        # Usuário só pode ver os agendamentos de seus próprios clientes ou se for admin
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        agendamentos = Agendamento.query.filter_by(cliente_id=cliente_id).order_by(
            Agendamento.data_hora.desc()
        ).all()
        return jsonify([a.to_dict() for a in agendamentos])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cliente_bp.route("/clientes/<int:cliente_id>/conversas", methods=["GET"])
@jwt_required()
def listar_conversas_cliente(cliente_id):
    """Lista todas as conversas de um cliente"""
    try:
        current_user_id = get_jwt_identity()
        current_user = Funcionaria.query.get(current_user_id)

        cliente = Cliente.query.get_or_404(cliente_id)

        # Usuário só pode ver as conversas de seus próprios clientes ou se for admin
        if not current_user.is_admin and cliente.funcionaria_id != current_user_id:
            return jsonify({"error": "Acesso não autorizado"}), 403

        conversas = Conversa.query.filter_by(cliente_id=cliente_id).order_by(
            Conversa.ultima_atividade.desc()
        ).all()
        return jsonify([c.to_dict() for c in conversas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

