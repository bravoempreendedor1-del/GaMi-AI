"""
Módulo do Cérebro - ChatOpenAI configurado para OpenRouter/Claude 3.5 Sonnet
com System Prompt dinâmico baseado em perfis de chat
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

# System Prompts por Perfil de Chat
SYSTEM_PROMPTS = {
    "modo_programador": """Você é o GaMi-AI em **Modo Programador**, um Engenheiro de Software Sênior especializado em:

- Desenvolvimento Python moderno (Python 3.10+)
- Arquitetura de software (Clean Architecture, DDD, SOLID)
- Frameworks: FastAPI, Chainlit, LangChain, SQLAlchemy
- Boas práticas: Type hints, Async/await, Testing
- Debugging avançado e otimização de performance
- CI/CD, Docker, Cloud (Railway, AWS, etc.)

Seja técnico, direto e forneça código funcional. Sempre explique decisões arquiteturais e sugira melhorias.""",

    "modo_consultor": """Você é o GaMi-AI em **Modo Consultor**, um Consultor de Negócios Estratégico especializado em:

- Análise estratégica e planejamento empresarial
- Gestão de projetos e metodologias ágeis
- Transformação digital e inovação
- Otimização de processos operacionais
- Análise de mercado e competitividade
- Estruturação de propostas e apresentações executivas

Seja analítico, objetivo e focado em resultados práticos. Forneça insights acionáveis.""",

    "modo_geral": """Você é o GaMi-AI, um Assistente Polímata versátil que combina:

**Engenharia de Software (Python)**
- Desenvolvimento de aplicações modernas
- Arquitetura de software e boas práticas
- Frameworks: FastAPI, Chainlit, LangChain

**Consultoria de Negócios**
- Análise estratégica e tomada de decisão
- Planejamento de projetos e gestão
- Otimização de processos

Você é experiente, direto ao ponto e sempre busca soluções práticas e eficientes.
Adapte seu tom e profundidade técnica conforme o contexto da pergunta."""
}


def obter_system_prompt(perfil: str = "modo_geral") -> str:
    """
    Retorna o system prompt baseado no perfil de chat selecionado.
    
    Args:
        perfil: Nome do perfil (modo_programador, modo_consultor, modo_geral)
        
    Returns:
        System prompt correspondente
    """
    return SYSTEM_PROMPTS.get(perfil, SYSTEM_PROMPTS["modo_geral"])


def criar_llm() -> ChatOpenAI:
    """
    Cria e configura o ChatOpenAI para usar OpenRouter com Claude 3.5 Sonnet.
    
    Returns:
        Instância configurada do ChatOpenAI
    """
    # Obter configurações do ambiente
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Validação da API key
    if not api_key:
        raise ValueError("OPENAI_API_KEY não configurada. Configure a variável de ambiente.")
    
    # Determina modelo baseado na base_url
    # Se usar OpenRouter, usa Claude. Se usar OpenAI direto, usa GPT
    if "openrouter.ai" in base_url:
        model_name = "anthropic/claude-3.5-sonnet"
    else:
        # Se usar OpenAI direto, tenta GPT-4o, senão usa GPT-3.5-turbo como fallback
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        # Fallback para modelos mais antigos se gpt-4o não estiver disponível
        if model_name not in ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]:
            model_name = "gpt-4o"  # Tenta gpt-4o primeiro
    
    print(f"🔧 Usando modelo: {model_name} | Base URL: {base_url}")
    
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        max_tokens=2000,
        timeout=60,  # Timeout de 60 segundos
    )
    
    return llm


def pensar(mensagem: str, system_prompt: str, historico: list = None) -> str:
    """
    Processa uma mensagem e retorna a resposta do assistente com system prompt dinâmico.
    
    Args:
        mensagem: Mensagem do usuário
        system_prompt: System prompt a ser usado (baseado no perfil)
        historico: Histórico de conversa (opcional) - lista de dicts com "role" e "content"
        
    Returns:
        Resposta do assistente
    """
    llm = criar_llm()
    
    # Preparar mensagens do LangChain com system prompt dinâmico
    mensagens = [SystemMessage(content=system_prompt)]
    
    # Adicionar histórico se fornecido (converter dicts para mensagens LangChain)
    if historico:
        for msg in historico:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                mensagens.append(HumanMessage(content=content))
            elif role == "assistant":
                mensagens.append(AIMessage(content=content))
    
    # Adicionar mensagem atual
    mensagens.append(HumanMessage(content=mensagem))
    
    # Obter resposta
    try:
        print(f"📤 Enviando mensagem para o modelo...")
        response = llm.invoke(mensagens)
        resposta_texto = response.content if hasattr(response, 'content') else str(response)
        print(f"✅ Resposta recebida ({len(resposta_texto)} caracteres)")
        return resposta_texto
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erro ao invocar modelo: {error_msg}")
        # Se for erro de modelo não encontrado, tenta fallback
        if "model" in error_msg.lower() and ("not found" in error_msg.lower() or "does not exist" in error_msg.lower()):
            # Tenta usar gpt-3.5-turbo como fallback
            print("🔄 Tentando fallback para gpt-3.5-turbo...")
            try:
                llm_fallback = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=60,
                )
                response = llm_fallback.invoke(mensagens)
                return response.content if hasattr(response, 'content') else str(response)
            except Exception as e2:
                raise Exception(f"Erro ao processar mensagem (tentativa com fallback também falhou): {str(e2)}")
        raise Exception(f"Erro ao processar mensagem: {error_msg}")
