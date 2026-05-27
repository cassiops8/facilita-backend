from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.log_auditoria import LogAuditoria
from src.models.funcionaria import Funcionaria
from datetime import datetime, timedelta

log_auditoria_bp = Blueprint('log_auditoria', __name__)

@log_auditoria_bp.route('/api/logs-auditoria', methods=['GET'])
def listar_logs():
    try:
        # Parâmetros de filtro
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        usuario_id = request.args.get('usuario_id', type=int)
        acao = request.args.get('acao')
        tabela = request.args.get('tabela')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Query base
        query = LogAuditoria.query
        
        # Aplicar filtros
        if usuario_id:
            query = query.filter(LogAuditoria.usuario_id == usuario_id)
        
        if acao:
            query = query.filter(LogAuditoria.acao == acao)
        
        if tabela:
            query = query.filter(LogAuditoria.tabela == tabela)
        
        if data_inicio:
            data_inicio_dt = datetime.fromisoformat(data_inicio)
            query = query.filter(LogAuditoria.data_hora >= data_inicio_dt)
        
        if data_fim:
            data_fim_dt = datetime.fromisoformat(data_fim)
            query = query.filter(LogAuditoria.data_hora <= data_fim_dt)
        
        # Ordenar por data mais recente
        query = query.order_by(LogAuditoria.data_hora.desc())
        
        # Paginação
        logs = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in logs.items],
            'total': logs.total,
            'pages': logs.pages,
            'current_page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@log_auditoria_bp.route('/api/logs-auditoria/resumo', methods=['GET'])
def resumo_logs():
    try:
        # Últimas 24 horas
        data_limite = datetime.utcnow() - timedelta(hours=24)
        
        # Contadores por ação
        logs_recentes = LogAuditoria.query.filter(LogAuditoria.data_hora >= data_limite).all()
        
        resumo = {
            'total_acoes_24h': len(logs_recentes),
            'acoes_por_tipo': {},
            'usuarios_mais_ativos': {},
            'tabelas_mais_alteradas': {}
        }
        
        # Contar ações por tipo
        for log in logs_recentes:
            if log.acao not in resumo['acoes_por_tipo']:
                resumo['acoes_por_tipo'][log.acao] = 0
            resumo['acoes_por_tipo'][log.acao] += 1
            
            # Contar por usuário
            usuario_nome = log.usuario.nome if log.usuario else 'Desconhecido'
            if usuario_nome not in resumo['usuarios_mais_ativos']:
                resumo['usuarios_mais_ativos'][usuario_nome] = 0
            resumo['usuarios_mais_ativos'][usuario_nome] += 1
            
            # Contar por tabela
            if log.tabela not in resumo['tabelas_mais_alteradas']:
                resumo['tabelas_mais_alteradas'][log.tabela] = 0
            resumo['tabelas_mais_alteradas'][log.tabela] += 1
        
        return jsonify(resumo)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@log_auditoria_bp.route('/api/logs-auditoria/<int:log_id>', methods=['GET'])
def detalhe_log(log_id):
    try:
        log = LogAuditoria.query.get_or_404(log_id)
        return jsonify(log.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

