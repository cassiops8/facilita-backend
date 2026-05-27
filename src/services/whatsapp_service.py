import requests
import json
from datetime import datetime
from src.models.conversa import Conversa, Mensagem
from src.models.cliente import Cliente
from src.models.user import db
from src.services.ia_service_deploy import IAService

class WhatsAppService:
    def __init__(self):
        # Configurações do WhatsApp Business API
        # Em produção, essas configurações viriam de variáveis de ambiente
        self.api_url = "https://graph.facebook.com/v17.0"
        self.phone_number_id = "YOUR_PHONE_NUMBER_ID"  # Configurar em produção
        self.access_token = "YOUR_ACCESS_TOKEN"  # Configurar em produção
        self.ia_service = IAService()
    
    def processar_webhook(self, webhook_data):
        """Processa webhooks recebidos do WhatsApp"""
        try:
            if not self._validar_webhook(webhook_data):
                return False
            
            # Extrair informações da mensagem
            entry = webhook_data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            if 'messages' not in value:
                return True  # Não é uma mensagem, ignorar
            
            mensagem_data = value['messages'][0]
            contato_data = value.get('contacts', [{}])[0]
            
            numero_whatsapp = mensagem_data['from']
            nome_contato = contato_data.get('profile', {}).get('name', 'Usuário')
            conteudo_mensagem = self._extrair_conteudo_mensagem(mensagem_data)
            
            # Buscar ou criar conversa
            conversa = self._buscar_ou_criar_conversa(numero_whatsapp, nome_contato)
            
            # Salvar mensagem recebida
            self._salvar_mensagem(conversa.id, conteudo_mensagem, 'cliente')
            
            # Processar resposta automática se IA estiver ativa
            if conversa.modo_ia:
                resposta_ia = self.ia_service.processar_mensagem(conversa.id, conteudo_mensagem)
                if resposta_ia:
                    # Enviar resposta
                    self.enviar_mensagem(numero_whatsapp, resposta_ia)
                    # Salvar resposta da IA
                    self._salvar_mensagem(conversa.id, resposta_ia, 'ia')
            
            return True
            
        except Exception as e:
            print(f"Erro ao processar webhook: {e}")
            return False
    
    def enviar_mensagem(self, numero_destino, mensagem):
        """Envia uma mensagem via WhatsApp Business API"""
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': numero_destino,
                'type': 'text',
                'text': {
                    'body': mensagem
                }
            }
            
            # Em desenvolvimento, apenas simular o envio
            if self.access_token == "YOUR_ACCESS_TOKEN":
                print(f"[SIMULAÇÃO] Enviando para {numero_destino}: {mensagem}")
                return True
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return True
            else:
                print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return False
    
    def _validar_webhook(self, webhook_data):
        """Valida se o webhook é válido"""
        # Implementar validação de assinatura em produção
        return True
    
    def _extrair_conteudo_mensagem(self, mensagem_data):
        """Extrai o conteúdo da mensagem baseado no tipo"""
        tipo = mensagem_data.get('type', 'text')
        
        if tipo == 'text':
            return mensagem_data.get('text', {}).get('body', '')
        elif tipo == 'image':
            return '[Imagem enviada]'
        elif tipo == 'audio':
            return '[Áudio enviado]'
        elif tipo == 'document':
            return '[Documento enviado]'
        else:
            return '[Mensagem não suportada]'
    
    def _buscar_ou_criar_conversa(self, numero_whatsapp, nome_contato):
        """Busca uma conversa existente ou cria uma nova"""
        # Buscar conversa existente
        conversa = Conversa.query.filter_by(numero_whatsapp=numero_whatsapp).first()
        
        if conversa:
            # Atualizar última atividade
            conversa.ultima_atividade = datetime.utcnow()
            conversa.nome_contato = nome_contato  # Atualizar nome se mudou
            db.session.commit()
            return conversa
        
        # Tentar encontrar cliente pelo número
        cliente = Cliente.query.filter_by(telefone=numero_whatsapp).first()
        
        if not cliente:
            # Criar cliente temporário (será associado manualmente depois)
            cliente = Cliente(
                nome=nome_contato,
                telefone=numero_whatsapp,
                tipo_profissional='Não definido',
                funcionaria_id=1  # Atribuir à primeira funcionária por padrão
            )
            db.session.add(cliente)
            db.session.flush()  # Para obter o ID
        
        # Criar nova conversa
        conversa = Conversa(
            numero_whatsapp=numero_whatsapp,
            nome_contato=nome_contato,
            cliente_id=cliente.id,
            modo_ia=True  # IA ativa por padrão
        )
        
        db.session.add(conversa)
        db.session.commit()
        
        return conversa
    
    def _salvar_mensagem(self, conversa_id, conteudo, remetente, funcionaria_id=None):
        """Salva uma mensagem no banco de dados"""
        mensagem = Mensagem(
            conteudo=conteudo,
            remetente=remetente,
            conversa_id=conversa_id,
            funcionaria_id=funcionaria_id
        )
        
        db.session.add(mensagem)
        
        # Atualizar última atividade da conversa
        conversa = Conversa.query.get(conversa_id)
        if conversa:
            conversa.ultima_atividade = datetime.utcnow()
        
        db.session.commit()
    
    def alternar_modo_ia(self, conversa_id, modo_ia):
        """Alterna entre modo IA e modo manual"""
        conversa = Conversa.query.get(conversa_id)
        if conversa:
            conversa.modo_ia = modo_ia
            db.session.commit()
            return True
        return False
    
    def enviar_mensagem_funcionaria(self, conversa_id, mensagem, funcionaria_id):
        """Envia mensagem de uma funcionária"""
        conversa = Conversa.query.get(conversa_id)
        if not conversa:
            return False
        
        # Enviar via WhatsApp
        sucesso = self.enviar_mensagem(conversa.numero_whatsapp, mensagem)
        
        if sucesso:
            # Salvar no banco
            self._salvar_mensagem(conversa_id, mensagem, 'funcionaria', funcionaria_id)
            return True
        
        return False

