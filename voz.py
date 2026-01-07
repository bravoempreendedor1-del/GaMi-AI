"""
Módulo de Voz - Whisper (Transcrição) e OpenAI TTS (Fala)
"""
import os
import tempfile
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Inicializar cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcrever(audio_file_path: str) -> str:
    """
    Transcreve um arquivo de áudio usando Whisper.
    
    Args:
        audio_file_path: Caminho para o arquivo de áudio
        
    Returns:
        Texto transcrito
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt"  # Português
            )
        return transcript.text
    except Exception as e:
        raise Exception(f"Erro ao transcrever áudio: {str(e)}")


def falar(texto: str, voz: str = "onyx") -> str:
    """
    Converte texto em fala usando OpenAI TTS e salva o arquivo.
    
    Args:
        texto: Texto a ser convertido em fala
        voz: Voz a ser usada (alloy, echo, fable, onyx, nova, shimmer)
        
    Returns:
        Caminho do arquivo de áudio gerado
    """
    try:
        # Criar diretório de áudio no projeto (acessível pelo Chainlit)
        audio_dir = Path("audio")
        audio_dir.mkdir(exist_ok=True)
        
        # Gerar nome único para o arquivo
        import uuid
        audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        audio_path = audio_dir / audio_filename
        
        # Gerar áudio usando OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",
            voice=voz,
            input=texto,
            response_format="mp3"
        )
        
        # Salvar arquivo
        with open(audio_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
        
        # Retornar caminho absoluto
        return str(audio_path.absolute())
    except Exception as e:
        raise Exception(f"Erro ao gerar fala: {str(e)}")

