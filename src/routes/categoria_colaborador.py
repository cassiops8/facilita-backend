from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.categoria_colaborador import CategoriaColaborador
from src.models.log_auditoria import LogAuditoria
import json

categoria_colaborador_bp = Blueprint('categoria_colaborador', __name__)

@categoria_colaborador_bp.route('/api/categorias-colaborador', methods=['GET'])
def listar_categorias():
    try:
        categorias = CategoriaColaborador.query.filter_by(ativo=True).all()
        return jsonify([categoria.to_dict() for categoria in categorias])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@categoria_colaborador_bp.route('/api/categorias-colaborador', methods=['POST'])
def criar_categoria():
    try:
        data = request.get_json()
        
        # Verificar se já existe uma categoria com o mesmo nome
        categoria_existente = CategoriaColaborador.query.filter_by(nome=data['nome']).first()
        if categoria_existente:
            return jsonify({'error': 'Já existe uma categoria com este nome'}), 400
        
        categoria = CategoriaColaborador(
            nome=data['nome'],
            descricao=data.get('descricao', ''),
        )
        
        db.session.add(categoria)
        db.session.commit()
        
        # Log de auditoria
        log = LogAuditoria(
            usuario_id=data.get('usuario_id', 1),  # TODO: pegar do token de autenticação
            acao='CREATE',
            tabela='categorias_colaborador',
            registro_id=categoria.id,
            dados_novos=json.dumps(categoria.to_dict())
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(categoria.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@categoria_colaborador_bp.route('/api/categorias-colaborador/<int:categoria_id>', methods=['PUT'])
def atualizar_categoria(categoria_id):
    try:
        categoria = CategoriaColaborador.query.get_or_404(categoria_id)
        data = request.get_json()
        
        dados_anteriores = categoria.to_dict()
        
        categoria.nome = data.get('nome', categoria.nome)
        categoria.descricao = data.get('descricao', categoria.descricao)
        categoria.ativo = data.get('ativo', categoria.ativo)
        
        db.session.commit()
        
        # Log de auditoria
        log = LogAuditoria(
            usuario_id=data.get('usuario_id', 1),  # TODO: pegar do token de autenticação
            acao='UPDATE',
            tabela='categorias_colaborador',
            registro_id=categoria.id,
            dados_anteriores=json.dumps(dados_anteriores),
            dados_novos=json.dumps(categoria.to_dict())
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(categoria.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@categoria_colaborador_bp.route('/api/categorias-colaborador/<int:categoria_id>', methods=['DELETE'])
def deletar_categoria(categoria_id):
    try:
        categoria = CategoriaColaborador.query.get_or_404(categoria_id)
        data = request.get_json() or {}
        
        dados_anteriores = categoria.to_dict()
        
        # Soft delete
        categoria.ativo = False
        db.session.commit()
        
        # Log de auditoria
        log = LogAuditoria(
            usuario_id=data.get('usuario_id', 1),  # TODO: pegar do token de autenticação
            acao='DELETE',
            tabela='categorias_colaborador',
            registro_id=categoria.id,
            dados_anteriores=json.dumps(dados_anteriores)
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Categoria desativada com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

