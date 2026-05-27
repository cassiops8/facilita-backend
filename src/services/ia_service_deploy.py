from datetime import datetime, timedelta
from src.models.cliente import Cliente
from src.models.agendamento import Agendamento
from src.models.conversa import Conversa, Mensagem
from src.models.user import db

class IAService:
    def __init__(self):
        # Versão simplificada para deploy
        pass
    
    def processar_mensagem(self, conversa_id, mensagem_cliente):
        """Processa uma mensagem do cliente e gera uma resposta da IA"""
        try:
            conversa = Conversa.query.get(conversa_id)
            if not conversa or not conversa.modo_ia:
                return None
            
            cliente = Cliente.query.get(conversa.cliente_id)
            if not cliente:
                return None
            
            # Resposta padrão inteligente baseada na mensagem
            mensagem_lower = mensagem_cliente.lower()
            
            if any(palavra in mensagem_lower for palavra in ['agendar', 'marcar', 'consulta', 'horário']):
                return f"Olá! Claro, posso ajudar com o agendamento. Para {cliente.especialidade}, temos disponibilidade esta semana. Qual seria o melhor dia e horário para você?"
            
            elif any(palavra in mensagem_lower for palavra in ['cancelar', 'desmarcar', 'reagendar']):
                return "Entendi que você precisa alterar um agendamento. Vou verificar sua agenda e te ajudo com isso. Pode me informar qual procedimento você gostaria de alterar?"
            
            elif any(palavra in mensagem_lower for palavra in ['preço', 'valor', 'quanto custa']):
                return f"Para informações sobre valores dos procedimentos de {cliente.especialidade}, vou verificar nossa tabela atualizada e retorno em instantes."
            
            elif any(palavra in mensagem_lower for palavra in ['preparo', 'cuidados', 'antes', 'depois']):
                return "Sobre os cuidados pré e pós-procedimento, vou te enviar todas as orientações necessárias. É muito importante seguir essas recomendações para o melhor resultado."
            
            elif any(palavra in mensagem_lower for palavra in ['olá', 'oi', 'bom dia', 'boa tarde', 'boa noite']):
                return f"Olá! Sou a assistente virtual da {cliente.nome}. Como posso ajudá-lo hoje? Posso auxiliar com agendamentos, informações sobre procedimentos e dúvidas gerais."
            
            else:
                respostas_gerais = [
                    f"Obrigada pelo contato! Sou a assistente da {cliente.nome}. Como posso ajudá-lo?",
                    "Entendi sua solicitação. Vou verificar as informações e retorno em instantes.",
                    "Perfeito! Deixe-me consultar nossa agenda e já te respondo.",
                    "Recebi sua mensagem. Vou verificar os detalhes e entro em contato.",
                    f"Olá! Para {cliente.especialidade}, posso ajudar com agendamentos e informações. O que você precisa?"
                ]
                
                # Selecionar resposta baseada no comprimento da mensagem
                indice = len(mensagem_cliente) % len(respostas_gerais)
                return respostas_gerais[indice]
            
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
            return "Desculpe, ocorreu um erro. Uma funcionária irá te atender em breve."
    
    def criar_agendamento_automatico(self, conversa_id, dados_agendamento):
        """Cria um agendamento automaticamente baseado na conversa"""
        try:
            conversa = Conversa.query.get(conversa_id)
            if not conversa:
                return False
            
            cliente = Cliente.query.get(conversa.cliente_id)
            if not cliente:
                return False
            
            # Criar o agendamento
            agendamento = Agendamento(
                titulo=dados_agendamento.get('titulo', 'Agendamento via WhatsApp'),
                descricao=dados_agendamento.get('descricao', ''),
                data_hora=datetime.fromisoformat(dados_agendamento['data_hora']),
                duracao_minutos=dados_agendamento.get('duracao_minutos', 60),
                tipo=dados_agendamento.get('tipo', 'consulta'),
                local=dados_agendamento.get('local', ''),
                observacoes=dados_agendamento.get('observacoes', 'Agendado via IA'),
                cliente_id=cliente.id,
                nome_paciente=dados_agendamento['nome_paciente'],
                telefone_paciente=dados_agendamento.get('telefone_paciente', ''),
                email_paciente=dados_agendamento.get('email_paciente', ''),
                status='agendado'
            )
            
            db.session.add(agendamento)
            db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Erro ao criar agendamento automático: {e}")
            return False
    
    def verificar_disponibilidade(self, cliente_id, data_hora, duracao_minutos=60):
        """Verifica se um horário está disponível para agendamento"""
        try:
            data_inicio = datetime.fromisoformat(data_hora)
            data_fim = data_inicio + timedelta(minutes=duracao_minutos)
            
            # Verificar conflitos de agendamento
            conflitos = Agendamento.query.filter(
                Agendamento.cliente_id == cliente_id,
                Agendamento.status.in_(['agendado', 'confirmado']),
                Agendamento.data_hora < data_fim,
                Agendamento.data_hora + timedelta(minutes=Agendamento.duracao_minutos) > data_inicio
            ).count()
            
            return conflitos == 0
            
        except Exception as e:
            print(f"Erro ao verificar disponibilidade: {e}")
            return False

