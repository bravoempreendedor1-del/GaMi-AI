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
# IMPORTANTE: Este módulo é importado depois de app.py, então usa a mesma lógica
DATABASE_URL = os.getenv("DATABASE_URL")
usar_sqlite = False

if DATABASE_URL:
    # Se detecta railway.internal, testa se consegue conectar
    if "railway.internal" in DATABASE_URL:
        try:
            from sqlalchemy import text
            # Ajusta URL
            if DATABASE_URL.startswith("postgres://"):
                DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            
            test_engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 2, "sslmode": "require"}
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            test_engine.dispose()
            print(f"✅ Conectado ao PostgreSQL (Produção)")
        except Exception:
            # Não conseguiu conectar = está local
            usar_sqlite = True
            DATABASE_URL = "sqlite:///chainlit.db"
            print(f"🔄 Modo Local (database.py)")
    elif "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
        # PostgreSQL sem railway.internal
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        print(f"✅ Conectado ao PostgreSQL (database.py)")
    else:
        # URL desconhecida, usa SQLite
        usar_sqlite = True
        DATABASE_URL = "sqlite:///chainlit.db"
else:
    # Sem DATABASE_URL
    usar_sqlite = True
    DATABASE_URL = "sqlite:///chainlit.db"

# Configura engine baseado na detecção
if usar_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    print(f"✅ Conectado ao SQLite (Local): {DATABASE_URL}")
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"} if "postgresql" in DATABASE_URL else {}
    )


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

