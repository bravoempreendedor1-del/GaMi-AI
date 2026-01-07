"""
Configuração do Banco de Dados - Lógica Dual (PostgreSQL/SQLite)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from models import Base, ChatProfile, Message
from dotenv import load_dotenv

load_dotenv()

# Lógica Dual: Verifica DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Produção/Railway: Usa PostgreSQL
    # DATABASE_URL já vem no formato correto (postgresql://user:pass@host/db)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print(f"✅ Conectado ao PostgreSQL (Produção)")
else:
    # Local: Usa SQLite
    DATABASE_URL = "sqlite:///chainlit.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Necessário para SQLite
        poolclass=StaticPool
    )
    print(f"✅ Conectado ao SQLite (Local): {DATABASE_URL}")


# Criar todas as tabelas
def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas/verificadas no banco de dados")


# Session Local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Retorna uma sessão do banco de dados (dependency injection).
    
    Yields:
        Session: Sessão do SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_perfis_padrao(db: Session):
    """
    Cria os perfis padrão se não existirem.
    
    Args:
        db: Sessão do banco de dados
    """
    perfis_padrao = [
        {"name": "modo_programador", "description": "Especialista em Engenharia de Software Python"},
        {"name": "modo_consultor", "description": "Consultor de Negócios Estratégico"},
        {"name": "modo_geral", "description": "Assistente Polímata Versátil"}
    ]
    
    for perfil_data in perfis_padrao:
        perfil_existente = db.query(ChatProfile).filter(
            ChatProfile.name == perfil_data["name"]
        ).first()
        
        if not perfil_existente:
            novo_perfil = ChatProfile(**perfil_data)
            db.add(novo_perfil)
    
    db.commit()
    print("✅ Perfis padrão criados/verificados")

