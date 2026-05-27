import os
import openai
from datetime import datetime, timedelta
from src.models.cliente import Cliente
from src.models.agendamento import Agendamento
from src.models.conversa import Conversa, Mensagem
from src.models.user import db

class IAService:
    def __init__(self):
        # Configurar OpenAI
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        )
        
        # Prompt base para o assistente
        self.prompt_base = """
Você é um assistente virtual especializado em secretariado remoto para profissionais da área de beleza e saúde feminina.

Suas responsabilidades incluem:
- Agendar consultas e procedimentos
- Responder dúvidas sobre serviços
- Confirmar horários e reagendar quando necessário
- Fornecer informações sobre preparos pré e pós-procedimentos
- Manter um tom profissional, cordial e acolhedor

Diretrizes importantes:
- Sempre confirme informações importantes antes de finalizar agendamentos
- Se não souber uma informação específica, informe que irá verificar com o profissional
- Mantenha a conversa focada nos serviços oferecidos
- Use linguagem clara e acessível
- Seja empática e atenciosa com as necessidades das clientes

Contexto do cliente: {contexto_cliente}
Histórico da conversa: {historico_conversa}
"""
    
    def processar_mensagem(self, conversa_id, mensagem_cliente):
        """Processa uma mensagem do cliente e gera uma resposta da IA"""
        try:
            conversa = Conversa.query.get(conversa_id)
            if not conversa or not conversa.modo_ia:
                return None
            
            cliente = Cliente.query.get(conversa.cliente_id)
            if not cliente:
                return None
            
            # Buscar histórico da conversa
            historico = self._obter_historico_conversa(conversa_id)
            
            # Preparar contexto
            contexto_cliente = self._preparar_contexto_cliente(cliente)
            
            # Preparar prompt
            prompt = self.prompt_base.format(
                contexto_cliente=contexto_cliente,
                historico_conversa=historico
            )
            
            # Chamar OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": mensagem_cliente}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            resposta_ia = response.choices[0].message.content.strip()
            
            # Verificar se a mensagem contém solicitação de agendamento
            if self._detectar_solicitacao_agendamento(mensagem_cliente):
                dados_agendamento = self._extrair_dados_agendamento(mensagem_cliente, resposta_ia)
                if dados_agendamento:
                    self._sugerir_agendamento(conversa_id, dados_agendamento)
            
            return resposta_ia
            
        except Exception as e:
            print(f"Erro ao processar mensagem com IA: {e}")
            # Fallback para resposta padrão
            return self._resposta_fallback(mensagem_cliente)
    
    def _obter_historico_conversa(self, conversa_id, limite=10):
        """Obtém o histórico recente da conversa"""
        mensagens = Mensagem.query.filter_by(
            conversa_id=conversa_id
        ).order_by(Mensagem.data_envio.desc()).limit(limite).all()
        
        historico = []
        for msg in reversed(mensagens):
            papel = "Cliente" if msg.de_cliente else "Assistente"
            historico.append(f"{papel}: {msg.conteudo}")
        
        return "\n".join(historico[-5:])  # Últimas 5 mensagens
    
    def _preparar_contexto_cliente(self, cliente):
        """Prepara o contexto sobre o cliente"""
        contexto = f"""
Nome do profissional: {cliente.nome}
Especialidade: {cliente.especialidade}
Telefone: {cliente.telefone}
Email: {cliente.email}
"""
        
        # Adicionar informações sobre agendamentos recentes
        agendamentos_recentes = Agendamento.query.filter_by(
            cliente_id=cliente.id
        ).order_by(Agendamento.data_hora.desc()).limit(3).all()
        
        if agendamentos_recentes:
            contexto += "\nAgendamentos recentes:\n"
            for ag in agendamentos_recentes:
                contexto += f"- {ag.titulo} em {ag.data_hora.strftime('%d/%m/%Y %H:%M')} ({ag.status})\n"
        
        return contexto
    
    def _detectar_solicitacao_agendamento(self, mensagem):
        """Detecta se a mensagem contém uma solicitação de agendamento"""
        palavras_chave = [
            'agendar', 'marcar', 'consulta', 'horário', 'disponibilidade',
            'quando', 'pode', 'atender', 'procedimento', 'sessão'
        ]
        
        mensagem_lower = mensagem.lower()
        return any(palavra in mensagem_lower for palavra in palavras_chave)
    
    def _extrair_dados_agendamento(self, mensagem_cliente, resposta_ia):
        """Extrai dados de agendamento da conversa usando IA"""
        try:
            prompt_extracao = f"""
Analise a seguinte conversa e extraia informações de agendamento em formato JSON.
Se não houver informações suficientes, retorne null.

Mensagem do cliente: {mensagem_cliente}
Resposta do assistente: {resposta_ia}

Extraia:
- tipo_procedimento: string (ex: "consulta", "limpeza de pele", "botox")
- data_preferida: string no formato YYYY-MM-DD (se mencionada)
- horario_preferido: string no formato HH:MM (se mencionado)
- nome_paciente: string (se mencionado)
- telefone_paciente: string (se mencionado)
- observacoes: string (qualquer observação especial)

Retorne apenas o JSON ou null se não houver dados suficientes.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt_extracao}],
                max_tokens=200,
                temperature=0.3
            )
            
            resultado = response.choices[0].message.content.strip()
            
            # Tentar parsear JSON
            import json
            try:
                dados = json.loads(resultado)
                return dados if dados else None
            except:
                return None
                
        except Exception as e:
            print(f"Erro ao extrair dados de agendamento: {e}")
            return None
    
    def _sugerir_agendamento(self, conversa_id, dados_agendamento):
        """Sugere um agendamento baseado nos dados extraídos"""
        # Esta função pode ser expandida para criar sugestões de horários
        # Por enquanto, apenas registra a intenção
        print(f"Sugestão de agendamento detectada: {dados_agendamento}")
    
    def _resposta_fallback(self, mensagem_cliente):
        """Resposta de fallback quando a IA não está disponível"""
        respostas_padrao = [
            "Obrigada pelo contato! Vou verificar essa informação e retorno em instantes.",
            "Entendi sua solicitação. Deixe-me consultar a agenda e já te respondo.",
            "Perfeito! Vou verificar a disponibilidade e entro em contato.",
            "Recebi sua mensagem. Uma de nossas atendentes irá te responder em breve.",
            "Obrigada! Estou verificando as informações e já retorno o contato."
        ]
        
        # Selecionar resposta baseada no comprimento da mensagem
        indice = len(mensagem_cliente) % len(respostas_padrao)
        return respostas_padrao[indice]
    
    def criar_agendamento_automatico(self, conversa_id, dados_agendamento):
        """Cria um agendamento automaticamente baseado na conversa"""
        try:
            conversa = Conversa.query.get(conversa_id)
            if not conversa:
                return False
            
            cliente = Cliente.query.get(conversa.cliente_id)
            if not cliente:
                return False
            
            # Validar dados obrigatórios
            if not dados_agendamento.get('data_hora'):
                return False
            
            # Verificar disponibilidade
            data_hora = datetime.fromisoformat(dados_agendamento['data_hora'])
            if not self.verificar_disponibilidade(cliente.id, data_hora.isoformat()):
                return False
            
            # Criar o agendamento
            agendamento = Agendamento(
                titulo=dados_agendamento.get('titulo', 'Agendamento via WhatsApp'),
                descricao=dados_agendamento.get('descricao', ''),
                data_hora=data_hora,
                duracao_minutos=dados_agendamento.get('duracao_minutos', 60),
                tipo=dados_agendamento.get('tipo', 'consulta'),
                local=dados_agendamento.get('local', ''),
                observacoes=dados_agendamento.get('observacoes', 'Agendado via IA'),
                cliente_id=cliente.id,
                nome_paciente=dados_agendamento.get('nome_paciente', ''),
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
    
    def gerar_sugestoes_horarios(self, cliente_id, data_preferida, duracao_minutos=60):
        """Gera sugestões de horários disponíveis"""
        try:
            data_base = datetime.fromisoformat(data_preferida) if isinstance(data_preferida, str) else data_preferida
            sugestoes = []
            
            # Horários comerciais típicos (9h às 18h)
            horarios_base = [9, 10, 11, 14, 15, 16, 17]
            
            for hora in horarios_base:
                data_teste = data_base.replace(hour=hora, minute=0, second=0, microsecond=0)
                
                if self.verificar_disponibilidade(cliente_id, data_teste.isoformat(), duracao_minutos):
                    sugestoes.append({
                        'data_hora': data_teste.isoformat(),
                        'data_formatada': data_teste.strftime('%d/%m/%Y'),
                        'hora_formatada': data_teste.strftime('%H:%M'),
                        'disponivel': True
                    })
                
                if len(sugestoes) >= 3:  # Limitar a 3 sugestões
                    break
            
            return sugestoes
            
        except Exception as e:
            print(f"Erro ao gerar sugestões de horários: {e}")
            return []

