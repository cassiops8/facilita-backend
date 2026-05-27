import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import db
from src.models.funcionaria import Funcionaria
from src.main import app

with app.app_context():
    admin_email = 'cassiops7@gmail.com'
    admin_password = 'F1234567'
    
    admin_user = Funcionaria.query.filter_by(email=admin_email).first()
    
    if not admin_user:
        print("Usuário administrador não encontrado. Criando...")
        admin_user = Funcionaria(
            nome='Administrador Principal',
            email=admin_email,
            senha=generate_password_hash(admin_password),
            telefone='(11) 99999-0000',
            is_admin=True,
            ativa=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Usuário administrador criado com sucesso!")
    else:
        print("Usuário administrador encontrado.")
        if not check_password_hash(admin_user.senha, admin_password):
            print("Senha do administrador incorreta. Atualizando...")
            admin_user.senha = generate_password_hash(admin_password)
            db.session.commit()
            print("Senha do administrador atualizada com sucesso!")
        else:
            print("Senha do administrador já está correta.")

    print(f"Admin user found: {admin_user is not None}")
    print(f"Is password correct: {check_password_hash(admin_user.senha, admin_password)}")


