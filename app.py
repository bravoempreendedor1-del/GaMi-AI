"""
GaMi-AI - Main Application
Sistema Polímata com Visual ChatGPT, Perfis e Persistência Híbrida.
"""
import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from sqlalchemy import create_engine
from voz import transcrever, falar
from cerebro import pensar, obter_system_prompt
from database import SessionLocal, init_db, criar_perfis_padrao, get_db
from sqlalchemy.pool import StaticPool
from models import ChatProfile, Message
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# 1. CONFIGURAÇÃO DO BANCO DE DADOS (LOCAL vs SERVIDOR - LÓGICA HÍBRIDA)
# ============================================================================

# Variável global para controlar qual banco usar
_USE_SQLITE_LOCAL = False
_DATABASE_URL_FINAL = None

def configurar_banco():
    """Tenta conectar ao Postgres. Se falhar, usa SQLite local."""
    global _USE_SQLITE_LOCAL, _DATABASE_URL_FINAL
    
    database_url = os.environ.get("DATABASE_URL")
    
    # Se não há DATABASE_URL, usa SQLite
    if not database_url:
        _USE_SQLITE_LOCAL = True
        _DATABASE_URL_FINAL = "sqlite:///chainlit.db"
    # Se detecta railway.internal, testa conexão
    elif "railway.internal" in database_url:
        # Tenta conexão com timeout curto para ver se estamos no servidor
        try:
            from sqlalchemy import create_engine, text
            # Ajusta URL se necessário
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            
            engine_teste = create_engine(
                database_url, 
                pool_pre_ping=True, 
                connect_args={"connect_timeout": 2, "sslmode": "require"}
            )
            
            # Testa conexão
            with engine_teste.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine_teste.dispose()
            
            # Se conectou, está no Railway
            print("✅ BANCO ONLINE CONECTADO (PostgreSQL Railway)")
            _USE_SQLITE_LOCAL = False
            _DATABASE_URL_FINAL = database_url
            
            # Configura Chainlit para Produção
            cl.DataLayer = SQLAlchemyDataLayer(conninfo=database_url, ssl_args={"sslmode": "require"})
            return
            
        except Exception as e:
            # Falhou = está local
            print(f"🔄 Modo Local Ativado (não foi possível conectar ao Railway)")
            _USE_SQLITE_LOCAL = True
            _DATABASE_URL_FINAL = "sqlite:///chainlit.db"
    # URL PostgreSQL sem railway.internal (produção manual)
    elif "postgresql" in database_url or "postgres" in database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        print("✅ BANCO ONLINE (PostgreSQL)")
        _USE_SQLITE_LOCAL = False
        _DATABASE_URL_FINAL = database_url
        cl.DataLayer = SQLAlchemyDataLayer(conninfo=database_url, ssl_args={"sslmode": "require"})
        return
    else:
        # Qualquer outra URL desconhecida, usa SQLite
        _USE_SQLITE_LOCAL = True
        _DATABASE_URL_FINAL = "sqlite:///chainlit.db"

    # Configura SQLite Local
    if _USE_SQLITE_LOCAL:
        db_local = "sqlite+aiosqlite:///chainlit.db"
        try:
            # Configura o DataLayer do Chainlit
            cl.DataLayer = SQLAlchemyDataLayer(conninfo=db_local)
            # Força inicialização do storage client
            if hasattr(cl.DataLayer, 'init'):
                cl.DataLayer.init()
            print("✅ BANCO LOCAL ATIVADO (chainlit.db com aiosqlite)")
        except Exception as e:
            print(f"⚠️ Erro ao configurar DataLayer local: {e}")
            print("ℹ️ Continuando sem DataLayer do Chainlit (usando persistência customizada)")
            cl.DataLayer = None

# Executa a configuração
configurar_banco()

# Configura engine para nosso banco auxiliar (usado em database.py)
# Usa a mesma lógica determinada acima
if _USE_SQLITE_LOCAL:
    engine = create_engine(
        "sqlite:///chainlit.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    engine = create_engine(
        _DATABASE_URL_FINAL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"} if "postgresql" in _DATABASE_URL_FINAL else {}
    )

# Inicializa nosso banco auxiliar
init_db()
try:
    with SessionLocal() as db:
        criar_perfis_padrao(db)
except:
    pass

# ============================================================================
# 2. PERFIS DE CHAT (MENU INICIAL)
# ============================================================================

@cl.set_chat_profiles
async def chat_profiles():
    # OBS: O texto está alinhado à esquerda para evitar o bug visual "Raw Code"
    return [
        cl.ChatProfile(
            name="modo_programador",
            markdown_description="**Modo Dev Python**\n\nEspecialista em Código, Arquitetura e Debug.",
            icon="💻",
        ),
        cl.ChatProfile(
            name="modo_consultor",
            markdown_description="**Modo Negócios**\n\nEstratégia, Marketing e Análise de Mercado.",
            icon="📊",
        ),
        cl.ChatProfile(
            name="modo_geral",
            markdown_description="**Modo Padrão**\n\nAssistente Polímata Inteligente e Adaptável.",
            icon="🌟",
        ),
    ]

# ============================================================================
# 3. LÓGICA DO CHAT
# ============================================================================

@cl.on_chat_start
async def start():
    # Define o perfil - tratamento robusto para diferentes formatos
    perfil_nome = "modo_geral"  # Padrão
    
    try:
        # Tenta obter o perfil de diferentes formas
        chat_profile = cl.user_session.get("chat_profile")
        
        if chat_profile:
            # PRIORIDADE 1: Se for string, usa diretamente (mais comum)
            if isinstance(chat_profile, str):
                perfil_nome = chat_profile
            # PRIORIDADE 2: Se for dict, tenta acessar pela chave 'name'
            elif isinstance(chat_profile, dict):
                perfil_nome = chat_profile.get('name', 'modo_geral')
            # PRIORIDADE 3: Se for objeto com atributo 'name', acessa com try/except
            else:
                try:
                    if hasattr(chat_profile, 'name'):
                        perfil_nome = getattr(chat_profile, 'name', 'modo_geral')
                    else:
                        perfil_nome = "modo_geral"
                except (AttributeError, TypeError):
                    perfil_nome = "modo_geral"
    except Exception as e:
        print(f"⚠️ Erro ao obter perfil: {e}, usando padrão")
        perfil_nome = "modo_geral"
    
    # Garante que o perfil é válido
    if perfil_nome not in ["modo_programador", "modo_consultor", "modo_geral"]:
        perfil_nome = "modo_geral"
    
    # Gera ID único se não existir
    if not cl.user_session.get("thread_id"):
        import uuid
        cl.user_session.set("thread_id", str(uuid.uuid4()))

    # Carrega a personalidade
    system_prompt = obter_system_prompt(perfil_nome)
    cl.user_session.set("perfil", perfil_nome)
    cl.user_session.set("system_prompt", system_prompt)
    cl.user_session.set("historico", [])

    # Mensagem Inicial Limpa
    msg_texto = f"**GaMi-AI Ativado.**\nModo: `{perfil_nome}`"
    await cl.Message(content=msg_texto).send()


@cl.on_message
async def main(message: cl.Message):
    # Processa Texto
    texto = message.content
    if texto and texto.strip():
        await processar_interacao(texto)
    else:
        await cl.Message(content="⚠️ Por favor, envie uma mensagem válida.", type="warning").send()


@cl.on_audio_end
async def on_audio_end(audio: cl.Audio):
    # Processa Voz
    await cl.Message(content="👂 Ouvindo...", type="info").send()
    
    try:
        # Executa transcrição em thread separada
        # Tenta usar asyncio.to_thread se disponível (Python 3.9+), senão usa loop.run_in_executor
        try:
            texto = await asyncio.to_thread(transcrever, audio.path)
        except AttributeError:
            # Fallback para Python < 3.9
            loop = asyncio.get_event_loop()
            texto = await loop.run_in_executor(None, transcrever, audio.path)
        
        if texto and texto.strip():
            await cl.Message(content=f"🗣️ **Você:** {texto}").send()
            await processar_interacao(texto, responder_com_audio=True)
        else:
            await cl.Message(content="⚠️ Não entendi o áudio.", type="warning").send()
    except Exception as e:
        await cl.Message(content=f"⚠️ Erro ao transcrever áudio: {str(e)}", type="error").send()

# ============================================================================
# 4. PROCESSAMENTO CENTRAL (CÉREBRO + VOZ)
# ============================================================================

async def processar_interacao(texto_usuario, responder_com_audio=False):
    try:
        # Validação
        if not texto_usuario or not texto_usuario.strip():
            return
        
        # Recupera contexto
        system_prompt = cl.user_session.get("system_prompt")
        if not system_prompt:
            perfil = cl.user_session.get("perfil", "modo_geral")
            system_prompt = obter_system_prompt(perfil)
        
        historico = cl.user_session.get("historico", [])
        
        # 1. Pensar
        await cl.Message(content="🧠 Pensando...", type="info").send()
        
        # Executa pensamento em thread separada para não bloquear
        # Tenta usar asyncio.to_thread se disponível (Python 3.9+), senão usa loop.run_in_executor
        try:
            resposta = await asyncio.to_thread(pensar, texto_usuario, system_prompt, historico)
        except AttributeError:
            # Fallback para Python < 3.9
            loop = asyncio.get_event_loop()
            resposta = await loop.run_in_executor(None, lambda: pensar(texto_usuario, system_prompt, historico))
        
        # 2. Atualizar Memória Local
        historico.append({"role": "user", "content": texto_usuario})
        historico.append({"role": "assistant", "content": resposta})
        cl.user_session.set("historico", historico)
        
        # 3. Salvar no Banco Customizado (Backup) - Executa em background sem bloquear
        thread_id = cl.user_session.get("thread_id")
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())
            cl.user_session.set("thread_id", thread_id)
        
        perfil = cl.user_session.get("perfil", "modo_geral")
        if thread_id:
            # Executa backup em background sem bloquear
            def fazer_backup():
                try:
                    salvar_db_backup(thread_id, perfil, texto_usuario, resposta)
                except Exception as e:
                    print(f"⚠️ Erro backup DB: {e}")
            
            # Tenta usar asyncio.to_thread se disponível (Python 3.9+), senão usa loop.run_in_executor
            try:
                asyncio.create_task(asyncio.to_thread(fazer_backup))
            except AttributeError:
                # Fallback para Python < 3.9
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, fazer_backup)

        # 4. Responder (Texto)
        await cl.Message(content=resposta).send()
        
        # 5. Responder (Áudio - Se solicitado ou automático)
        if responder_com_audio or True: 
            if len(resposta) < 800:  # Evita ler textos gigantes
                try:
                    # Executa geração de áudio em thread separada
                    # Tenta usar asyncio.to_thread se disponível (Python 3.9+), senão usa loop.run_in_executor
                    try:
                        audio_path = await asyncio.to_thread(falar, resposta)
                    except AttributeError:
                        # Fallback para Python < 3.9
                        loop = asyncio.get_event_loop()
                        audio_path = await loop.run_in_executor(None, falar, resposta)
                    
                    if audio_path:
                        el_audio = cl.Audio(path=audio_path, name="voz")
                        await cl.Message(content="", elements=[el_audio]).send()
                except Exception as e:
                    print(f"⚠️ Erro ao gerar áudio: {e}")

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"❌ Erro completo: {traceback.format_exc()}")
        await cl.Message(
            content=f"❌ **Erro ao processar:** {error_msg}\n\nPor favor, tente novamente ou verifique os logs.",
            type="error"
        ).send()

def salvar_db_backup(tid, perfil, user_txt, ai_txt):
    """
    Salva mensagens no banco de dados customizado (backup).
    """
    if not tid:
        return
    
    db = None
    try:
        db = next(get_db())
        p_obj = db.query(ChatProfile).filter(ChatProfile.name == perfil).first()
        pid = p_obj.id if p_obj else None
        
        db.add(Message(thread_id=tid, profile_id=pid, role="user", content=user_txt))
        db.add(Message(thread_id=tid, profile_id=pid, role="assistant", content=ai_txt))
        db.commit()
    except Exception as e:
        if db:
            db.rollback()
        print(f"⚠️ Erro ao salvar backup no DB: {e}")
    finally:
        if db:
            db.close()