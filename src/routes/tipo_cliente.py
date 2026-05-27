from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.tipo_cliente import TipoCliente
from src.models.log_auditoria import LogAuditoria
import json

tipo_cliente_bp = Blueprint('tipo_cliente', __name__)

@tipo_cliente_bp.route('/api/tipos-cliente', methods=['GET'])
def listar_tipos():
    try:
        tipos = TipoCliente.query.filter_by(ativo=True).all()
        return jsonify([tipo.to_dict() for tipo in tipos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tipo_cliente_bp.route('/api/tipos-cliente', methods=['POST'])
def criar_tipo():
    try:
        data = request.get_json()
        
        # Verificar se já existe um tipo com o mesmo nome
        tipo_existente = TipoCliente.query.filter_by(nome=data['nome']).first()
        if tipo_existente:
            return jsonify({'error': 'Já existe um tipo de cliente com este nome'}), 400
        
        tipo = TipoCliente(
            nome=data['nome'],
            setor=data.get('setor', ''),
            descricao=data.get('descricao', ''),
        )
        
        db.session.add(tipo)
        db.session.commit()
        
        # Log de auditoria
        log = LogAuditoria(
            usuario_id=data.get('usuario_id', 1),  # TODO: pegar do token de autenticação
            acao='CREATE',
            tabela='tipos_cliente',
            registro_id=tipo.id,
            dados_novos=json.dumps(tipo.to_dict())
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(tipo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tipo_cliente_bp.route('/api/tipos-cliente/<int:tipo_id>', methods=['PUT'])
def atualizar_tipo(tipo_id):
    try:
        tipo = TipoCliente.query.get_or_404(tipo_id)
        data = request.get_json()
        
        dados_anteriores = tipo.to_dict()
        
        tipo.nome = data.get('nome', tipo.nome)
        tipo.setor = data.get('setor', tipo.setor)
        tipo.descricao = data.get('descricao', tipo.descricao)
        tipo.ativo = data.get('ativo', tipo.ativo)
        
        db.session.commit()
        
        # Log de auditoria
        log = LogAuditoria(
            usuario_id=data.get('usuario_id', 1),  # TODO: pegar do token de autenticação
            acao='UPDATE',
            tabela='tipos_cliente',
            registro_id=tipo.id,
            dados_anteriores=json.dumps(dados_anteriores),
            dados_novos=json.dumps(tipo.to_dict())
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(tipo.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tipo_cliente_bp.route('/api/tipos-cliente/<int:tipo_id>', methods=['DELETE'])
def deletar_tipo(tipo_id):
    try:
        tipo = TipoCliente.query.get_or_404(tipo_id)
        data = request.get_json() or {}
        
        dados_anteriores = tipo.to_dict()
        
        # Soft delete
        tipo.ativo = False
        db.session.commit()
        
        # Log de auditoria
        log = LogAuditoria(
            usuario_id=data.get('usuario_id', 1),  # TODO: pegar do token de autenticação
            acao='DELETE',
            tabela='tipos_cliente',
            registro_id=tipo.id,
            dados_anteriores=json.dumps(dados_anteriores)
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Tipo de cliente desativado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

