from enum import Enum
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    GROQ = "groq"


class LLMFactory:
    
    @staticmethod
    def create(
        provider: LLMProvider,
        model: str,
        temperature: float = 0.7,
        **kwargs: Any
    ):
        if provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                **kwargs
            )
        
        if provider == LLMProvider.GOOGLE:
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                **kwargs
            )
        
        if provider == LLMProvider.GROQ:
            return ChatGroq(
                model=model,
                temperature=temperature,
                **kwargs
            )
        
        raise ValueError(f"Proveedor no soportado: {provider}")