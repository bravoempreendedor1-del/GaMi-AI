"""
Modelos SQLAlchemy para persistência de dados
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class ChatProfile(Base):
    """
    Modelo para Perfis de Chat (simulam 'pastas' de contexto)
    """
    __tablename__ = "chat_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento com mensagens
    messages = relationship("Message", back_populates="profile", cascade="all, delete-orphan")


class Message(Base):
    """
    Modelo para mensagens do chat (histórico persistente)
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(255), nullable=False, index=True)  # ID da thread/sessão do Chainlit
    profile_id = Column(Integer, ForeignKey("chat_profiles.id"), nullable=True)
    role = Column(String(20), nullable=False)  # 'user' ou 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relacionamento com perfil
    profile = relationship("ChatProfile", back_populates="messages")

