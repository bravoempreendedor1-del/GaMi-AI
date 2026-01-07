#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Automação Git para GaMi-AI
Inicializa o repositório Git, configura .gitignore e faz commit inicial.
"""
import os
import subprocess
import sys
from pathlib import Path

# Configura encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_command(cmd, description):
    """Executa um comando do shell e trata erros."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False

def check_git_installed():
    """Verifica se o Git está instalado."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git não está instalado. Por favor, instale o Git primeiro.")
        return False

def main():
    """Função principal."""
    print("=" * 60)
    print("🚀 GaMi-AI - Setup Git Automation")
    print("=" * 60)
    print()
    
    # Verifica se Git está instalado
    if not check_git_installed():
        sys.exit(1)
    
    # Verifica se já é um repositório Git
    if Path(".git").exists():
        print("⚠️  Já existe um repositório Git neste diretório.")
        resposta = input("   Deseja continuar mesmo assim? (s/N): ").strip().lower()
        if resposta != 's':
            print("❌ Operação cancelada.")
            sys.exit(0)
    
    # 1. Inicializa o repositório Git
    if not Path(".git").exists():
        if not run_command("git init", "Inicializando repositório Git"):
            sys.exit(1)
    else:
        print("✅ Repositório Git já existe.")
    
    # 2. Verifica se .gitignore existe
    if not Path(".gitignore").exists():
        print("⚠️  Arquivo .gitignore não encontrado.")
        print("   Criando .gitignore padrão...")
        gitignore_content = """# Ambiente
.env
.venv
venv/
env/

# Áudio gerado
audio/
*.mp3
*.wav

# Banco de dados
*.db
*.sqlite
*.sqlite3
chainlit.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("✅ .gitignore criado.")
    else:
        print("✅ .gitignore já existe.")
    
    # 3. Adiciona todos os arquivos (exceto os ignorados)
    if not run_command("git add .", "Adicionando arquivos ao staging"):
        sys.exit(1)
    
    # 4. Verifica se há mudanças para commitar
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if not result.stdout.strip():
        print("ℹ️  Nenhuma mudança para commitar.")
        print("✅ Setup concluído!")
        return
    
    # 5. Faz o commit inicial
    commit_message = "GaMi-AI: Setup inicial - Chainlit, Voz, Perfis e Persistência"
    if not run_command(
        f'git commit -m "{commit_message}"',
        f"Fazendo commit inicial: {commit_message}"
    ):
        sys.exit(1)
    
    # 6. Configura branch main (se necessário)
    result = subprocess.run(
        "git branch --show-current",
        shell=True,
        capture_output=True,
        text=True
    )
    current_branch = result.stdout.strip()
    
    if current_branch != "main":
        if run_command("git branch -M main", "Renomeando branch para 'main'"):
            print("✅ Branch renomeada para 'main'.")
    
    # 7. Mostra status final
    print()
    print("=" * 60)
    print("✅ Setup Git concluído com sucesso!")
    print("=" * 60)
    print()
    print("📋 Próximos passos:")
    print("   1. Adicione o remote do GitHub:")
    print("      git remote add origin https://github.com/SEU_USUARIO/GaMi-AI.git")
    print()
    print("   2. Faça o push:")
    print("      git push -u origin main")
    print()
    print("   3. No Render.com:")
    print("      - Conecte o repositório GitHub")
    print("      - Use o Blueprint (render.yaml)")
    print("      - Configure OPENAI_API_KEY nas variáveis de ambiente")
    print()
    
    # Mostra status do repositório
    print("📊 Status do repositório:")
    run_command("git status", "Verificando status")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

