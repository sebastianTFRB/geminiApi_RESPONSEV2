# chroma_manager.py
import os
import chromadb
from chromadb.config import Settings
from pathlib import Path

# Carpeta base para persistencia
BASE_CHROMA_PATH = Path("./.chromadb_global")
BASE_CHROMA_PATH.mkdir(exist_ok=True)

# Singleton para el cliente de Chroma
_chroma_client = None

def get_chroma_client():
    """Devuelve una única instancia global de Chroma Client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.Client(Settings(persist_directory=str(BASE_CHROMA_PATH)))
    return _chroma_client

def get_collection(app_name: str):
    """Devuelve o crea la colección correspondiente a una app."""
    client = get_chroma_client()
    return client.get_or_create_collection(f"{app_name}_docs")
