import openai
import os
from datetime import datetime, timedelta
from src.models.cliente import Cliente
from src.models.agendamento import Agendamento
from src.models.conversa import Conversa, Mensagem
from src.models.user import db

class IAService:
    def __init__(self):
        # As variáveis de ambiente já estão configuradas no sandbox
        self.client = openai.OpenAI()
    
    def processar_mensagem(self, conversa_id, mensagem_cliente):
        """Processa uma mensagem do cliente e gera uma resposta da IA"""
        try:
            conversa = Conversa.query.get(conversa_id)
            if not conversa or not conversa.modo_ia:
                return None
            
            cliente = Cliente.query.get(conversa.cliente_id)
            if not cliente:
                return None
            
            # Buscar histórico de mensagens
            mensagens_historico = Mensagem.query.filter_by(
                conversa_id=conversa_id
            ).order_by(Mensagem.data_envio.desc()).limit(10).all()
            
            # Buscar agendamentos do cliente
            agendamentos = Agendamento.query.filter_by(
                cliente_id=cliente.id
            ).order_by(Agendamento.data_hora.desc()).limit(5).all()
            
            # Construir contexto para a IA
            contexto = self._construir_contexto(cliente, agendamentos, mensagens_historico)
            
            # Gerar resposta da IA
            resposta = self._gerar_resposta_ia(contexto, mensagem_cliente)
            
            return resposta
            
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
            return "Desculpe, ocorreu um erro. Uma funcionária irá te atender em breve."
    
    def _construir_contexto(self, cliente, agendamentos, mensagens_historico):
        """Constrói o contexto para a IA com informações do cliente"""
        contexto = f"""
Você é uma assistente virtual da Facilita AR, especializada em secretariado remoto para profissionais de beleza e saúde feminina.

INFORMAÇÕES DO CLIENTE:
- Nome: {cliente.nome}
- Tipo: {cliente.tipo_profissional}
- Telefone: {cliente.telefone}
- Email: {cliente.email or 'Não informado'}
- Endereço: {cliente.endereco or 'Não informado'}
- Observações: {cliente.observacoes or 'Nenhuma'}

AGENDAMENTOS RECENTES:
"""
        
        for agendamento in agendamentos:
            contexto += f"""
- {agendamento.titulo} - {agendamento.data_hora.strftime('%d/%m/%Y %H:%M')} 
  Paciente: {agendamento.nome_paciente}
  Status: {agendamento.status}
  Local: {agendamento.local or 'Não informado'}
"""
        
        contexto += f"""

HISTÓRICO DA CONVERSA (mais recente primeiro):
"""
        
        for mensagem in reversed(mensagens_historico):
            remetente = "Cliente" if mensagem.remetente == "cliente" else "Assistente"
            contexto += f"- {remetente}: {mensagem.conteudo}\n"
        
        contexto += f"""

INSTRUÇÕES:
1. Seja sempre cordial, profissional e prestativa
2. Ajude com agendamentos, reagendamentos e informações gerais
3. Para agendamentos, sempre pergunte: data/hora preferida, nome do paciente, tipo de procedimento
4. Se não souber algo específico, diga que vai verificar com o profissional
5. Mantenha respostas concisas e objetivas
6. Use linguagem brasileira informal mas respeitosa
7. Sempre confirme informações importantes antes de finalizar agendamentos
8. Se o cliente quiser cancelar algo, seja compreensiva e ofereça alternativas

RESPONDA APENAS COMO A ASSISTENTE VIRTUAL, SEM EXPLICAÇÕES ADICIONAIS.
"""
        
        return contexto
    
    def _gerar_resposta_ia(self, contexto, mensagem_cliente):
        """Gera resposta usando a API da OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": contexto},
                    {"role": "user", "content": mensagem_cliente}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Erro ao gerar resposta da IA: {e}")
            return "Desculpe, estou com dificuldades técnicas no momento. Uma funcionária irá te atender em breve."
    
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

