import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from src.models.user import db
from src.models.funcionaria import Funcionaria
from src.models.cliente import Cliente
from src.models.agendamento import Agendamento
from src.models.conversa import Conversa, Mensagem
from src.main import app

def criar_dados_teste():
    with app.app_context():
        # Limpar dados existentes

        
        # Criar funcionárias

        funcionaria1 = Funcionaria(
            nome="Maria Santos",
            email="maria@facilita.com",
            senha=generate_password_hash("123456"),
            telefone="(11) 98888-8888"
        )
        
        funcionaria2 = Funcionaria(
            nome="Carla Oliveira",
            email="carla@facilita.com",
            senha=generate_password_hash("123456"),
            telefone="(11) 97777-7777"
        )
        
        db.session.add_all([admin, admin_principal, funcionaria1, funcionaria2])
        db.session.commit()
        
        # Criar clientes para Maria
        cliente1 = Cliente(
            nome="Dr. João Pereira",
            telefone="(11) 96666-6666",
            email="joao@clinica.com",
            tipo_profissional="Médico Dermatologista",
            endereco="Rua das Flores, 123 - São Paulo/SP",
            observacoes="Especialista em tratamentos estéticos",
            funcionaria_id=funcionaria1.id
        )
        
        cliente2 = Cliente(
            nome="Dra. Patricia Lima",
            telefone="(11) 95555-5555",
            email="patricia@estetica.com",
            tipo_profissional="Esteticista",
            endereco="Av. Paulista, 456 - São Paulo/SP",
            observacoes="Foco em harmonização facial",
            funcionaria_id=funcionaria1.id
        )
        
        # Criar clientes para Carla
        cliente3 = Cliente(
            nome="Marcos Terapias",
            telefone="(11) 94444-4444",
            email="marcos@terapias.com",
            tipo_profissional="Massoterapeuta",
            endereco="Rua da Saúde, 789 - São Paulo/SP",
            observacoes="Massagens terapêuticas e relaxantes",
            funcionaria_id=funcionaria2.id
        )
        
        cliente4 = Cliente(
            nome="Dra. Fernanda Hair",
            telefone="(11) 93333-3333",
            email="fernanda@hair.com",
            tipo_profissional="Tricologista",
            endereco="Rua dos Cabelos, 321 - São Paulo/SP",
            observacoes="Especialista em queda de cabelo",
            funcionaria_id=funcionaria2.id
        )
        
        db.session.add_all([cliente1, cliente2, cliente3, cliente4])
        db.session.commit()
        
        # Criar agendamentos
        hoje = datetime.now()
        
        agendamentos = [
            Agendamento(
                titulo="Consulta Dermatológica",
                descricao="Avaliação de pele para tratamento",
                data_hora=hoje + timedelta(hours=2),
                duracao_minutos=60,
                tipo="consulta",
                local="Clínica Dr. João",
                nome_paciente="Ana Costa",
                telefone_paciente="(11) 92222-2222",
                cliente_id=cliente1.id,
                status="agendado"
            ),
            Agendamento(
                titulo="Harmonização Facial",
                descricao="Aplicação de ácido hialurônico",
                data_hora=hoje + timedelta(days=1, hours=3),
                duracao_minutos=90,
                tipo="procedimento",
                local="Estética Patricia",
                nome_paciente="Beatriz Silva",
                telefone_paciente="(11) 91111-1111",
                cliente_id=cliente2.id,
                status="confirmado"
            ),
            Agendamento(
                titulo="Massagem Relaxante",
                descricao="Sessão de 60 minutos",
                data_hora=hoje + timedelta(hours=4),
                duracao_minutos=60,
                tipo="terapia",
                local="Clínica Marcos",
                nome_paciente="Carlos Mendes",
                telefone_paciente="(11) 90000-0000",
                cliente_id=cliente3.id,
                status="agendado"
            )
        ]
        
        db.session.add_all(agendamentos)
        db.session.commit()
        
        # Criar conversas
        conversa1 = Conversa(
            numero_whatsapp="5511966666666",
            nome_contato="Dr. João Pereira",
            cliente_id=cliente1.id,
            modo_ia=True
        )
        
        conversa2 = Conversa(
            numero_whatsapp="5511955555555",
            nome_contato="Dra. Patricia Lima",
            cliente_id=cliente2.id,
            modo_ia=False
        )
        
        db.session.add_all([conversa1, conversa2])
        db.session.commit()
        
        # Criar mensagens
        mensagens = [
            Mensagem(
                conteudo="Olá! Gostaria de agendar uma consulta para amanhã.",
                remetente="cliente",
                conversa_id=conversa1.id
            ),
            Mensagem(
                conteudo="Olá! Claro, vou verificar a agenda do Dr. João. Que horário seria melhor para você?",
                remetente="ia",
                conversa_id=conversa1.id
            ),
            Mensagem(
                conteudo="Prefiro pela manhã, se possível.",
                remetente="cliente",
                conversa_id=conversa1.id
            ),
            Mensagem(
                conteudo="Oi! Preciso remarcar meu procedimento de hoje.",
                remetente="cliente",
                conversa_id=conversa2.id
            )
        ]
        
        db.session.add_all(mensagens)
        db.session.commit()
        
        print("✅ Dados de teste criados com sucesso!")
        print("\n📋 Funcionárias criadas:")
        print("- Admin Principal: cassiops7@gmail.com (senha: F1234567)")
        print("- Admin: admin@facilita.com (senha: 123456)")
        print("- Maria: maria@facilita.com (senha: 123456)")
        print("- Carla: carla@facilita.com (senha: 123456)")
        print("\n👥 Clientes criados:")
        print("- 2 clientes para Maria (Dr. João e Dra. Patricia)")
        print("- 2 clientes para Carla (Marcos e Dra. Fernanda)")
        print("\n📅 Agendamentos e conversas criados para teste")

if __name__ == "__main__":
    criar_dados_teste()

