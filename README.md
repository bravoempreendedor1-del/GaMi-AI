# 🚀 GaMi-AI - Deploy Automatizado no Render.com

Sistema Polímata com Chainlit, Interface de Voz, Perfis de Chat e Persistência de Dados.

## 📋 Estrutura do Projeto

```
GaMi-AI/
├── app.py                 # Aplicação principal Chainlit
├── cerebro.py             # Lógica do LLM (OpenRouter/Claude)
├── voz.py                 # Transcrição e TTS (Whisper + OpenAI)
├── models.py              # Modelos SQLAlchemy
├── database.py            # Configuração do banco de dados
├── requirements.txt       # Dependências Python
├── Dockerfile             # Container Docker
├── render.yaml            # Blueprint do Render.com
├── setup_git.py           # Script de automação Git
└── .chainlit/
    └── config.toml        # Configuração do Chainlit
```

## 🛠️ Setup Local

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sua_chave_aqui
OPENAI_BASE_URL=https://openrouter.ai/api/v1  # Opcional (para OpenRouter)
# ou
OPENAI_BASE_URL=https://api.openai.com/v1     # Para OpenAI direto
```

### 3. Executar Localmente

```bash
chainlit run app.py
```

## 🚀 Deploy no Render.com

### Opção 1: Usando Blueprint (Recomendado)

1. **Preparar o Repositório Git:**

   ```bash
   # Execute o script de setup
   python setup_git.py
   
   # Ou manualmente:
   git init
   git add .
   git commit -m "GaMi-AI: Setup inicial"
   git branch -M main
   ```

2. **Conectar ao GitHub:**

   ```bash
   git remote add origin https://github.com/SEU_USUARIO/GaMi-AI.git
   git push -u origin main
   ```

3. **No Render.com:**

   - Acesse [render.com](https://render.com)
   - Clique em **"New +"** → **"Blueprint"**
   - Cole a URL do seu repositório GitHub
   - O Render detectará automaticamente o `render.yaml`
   - Clique em **"Apply"**

4. **Configurar Variáveis de Ambiente:**

   No Dashboard do Render, vá em **Environment** e adicione:

   - `OPENAI_API_KEY`: Sua chave da OpenAI ou OpenRouter
   - `OPENAI_BASE_URL`: (Opcional) URL da API
     - Para OpenRouter: `https://openrouter.ai/api/v1`
     - Para OpenAI: `https://api.openai.com/v1` (ou deixe vazio)

5. **Aguardar Deploy:**

   - O Render criará automaticamente:
     - Web Service (aplicação Chainlit)
     - PostgreSQL Database
     - Link automático via `DATABASE_URL`

### Opção 2: Deploy Manual

1. **Criar Web Service:**
   - Type: `Web Service`
   - Environment: `Docker`
   - Dockerfile Path: `./Dockerfile`
   - Build Command: (deixar vazio)
   - Start Command: `chainlit run app.py --host 0.0.0.0 --port $PORT`

2. **Criar PostgreSQL Database:**
   - Type: `PostgreSQL`
   - Name: `gami-ai-db`
   - Plan: `Free` (ou `Starter`)

3. **Linkar Database ao Web Service:**
   - No Web Service, vá em **Environment**
   - Adicione variável `DATABASE_URL`:
     - Key: `DATABASE_URL`
     - Value: (selecione do Database criado)

## 🔧 Configuração do Banco de Dados

O sistema usa **lógica híbrida**:

- **Produção (Render):** Usa PostgreSQL automaticamente via `DATABASE_URL`
- **Local:** Usa SQLite (`chainlit.db`) se `DATABASE_URL` não existir

O código detecta automaticamente o ambiente e configura o banco adequadamente.

## 📝 Funcionalidades

### ✅ Perfis de Chat
- **Modo Programador:** Especialista em Python, Arquitetura e Debug
- **Modo Consultor:** Estratégia, Marketing e Análise de Mercado
- **Modo Geral:** Assistente Polímata Versátil

### ✅ Interface de Voz
- **Transcrição:** Whisper (OpenAI) para áudio → texto
- **TTS:** OpenAI TTS (modelo `tts-1`, voz `onyx`)
- Auto-play de respostas em áudio

### ✅ Persistência de Dados
- Histórico de conversas salvo no banco
- Perfis de chat persistidos
- Backup automático de mensagens

## 🐳 Docker

O `Dockerfile` está configurado para:
- Python 3.11-slim
- Instalação de dependências do sistema (gcc, postgresql-client)
- Instalação de dependências Python
- Execução do Chainlit na porta `$PORT`

## 📦 Dependências Principais

- `chainlit` - Framework web para LLM apps
- `openai` - API OpenAI (Whisper, TTS)
- `langchain` / `langchain_openai` - Integração com LLMs
- `sqlalchemy` - ORM para banco de dados
- `psycopg2-binary` - Driver PostgreSQL
- `python-dotenv` - Gerenciamento de variáveis de ambiente

## 🔍 Troubleshooting

### Erro: "Name or service not known"
- **Causa:** Tentativa de conectar ao banco com hostname inválido
- **Solução:** O código já desabilita o DataLayer do Chainlit automaticamente quando não há conexão válida

### Erro: "OPENAI_API_KEY não configurada"
- **Causa:** Variável de ambiente não configurada
- **Solução:** Configure `OPENAI_API_KEY` no Render Dashboard → Environment

### Erro: "400 Bad Request" na API
- **Causa:** Modelo não disponível ou base_url incorreta
- **Solução:** Verifique `OPENAI_BASE_URL` e o modelo configurado em `cerebro.py`

## 📄 Licença

Este projeto é privado e de uso pessoal.

## 👤 Autor

GaMi-AI - Sistema Polímata Inteligente

---

**Deploy Automatizado:** O `render.yaml` configura tudo automaticamente. Basta conectar o repositório GitHub no Render!

