# InteligenSchool/contexts_manager.py
import os
from pathlib import Path
from typing import List

BASE = Path("./InteligenSchool")   # mantén consistente con tu estructura
CONTEXTOS_BASE = BASE / "contextos_materia"
CONTEXTOS_BASE.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".txt", ".md"}

def ensure_materia_dir(materia_id: str) -> Path:
    d = CONTEXTOS_BASE / materia_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def save_contexto_file(materia_id: str, filename: str, content: bytes) -> dict:
    """
    Guarda el archivo (bytes) en la carpeta de la materia.
    Si filename no tiene extension la añadimos .txt por defecto.
    """
    d = ensure_materia_dir(materia_id)
    p = Path(filename)
    if not p.suffix:
        filename = f"{filename}.txt"
        p = Path(filename)
    if p.suffix.lower() not in ALLOWED_EXT:
        return {"error": "Extensión no permitida. Usa .txt o .md"}

    dest = d / p.name
    with open(dest, "wb") as f:
        f.write(content)
    return {"status": "ok", "materiaId": materia_id, "archivo": p.name}

def list_contextos(materia_id: str) -> List[str]:
    d = CONTEXTOS_BASE / materia_id
    if not d.exists():
        return []
    files = [f.name for f in sorted(d.iterdir()) if f.is_file() and f.suffix.lower() in ALLOWED_EXT]
    return files

def read_all_contextos_text(materia_id: str) -> str:
    """Une y devuelve todo el contenido de los archivos .txt/.md de la materia."""
    textos = []
    d = CONTEXTOS_BASE / materia_id
    if not d.exists():
        return ""
    for f in sorted(d.iterdir()):
        if f.is_file() and f.suffix.lower() in ALLOWED_EXT:
            try:
                textos.append(f.read_text(encoding="utf-8").strip())
            except Exception:
                # si hay un problema de lectura, lo ignoramos para no romper la ruta
                pass
    return "\n\n".join([t for t in textos if t])
