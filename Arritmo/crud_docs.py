# crud_docs.py
import os
from pathlib import Path
from chroma_manager import get_chroma_client, get_collection  # ✅ usamos la fuente global

# ============================
# ⚙️ Configuración general
# ============================
APP_NAME = "Arritmo"

# Rutas locales
BASE_PATH = Path(f"./{APP_NAME}")
DOCS_PATH = BASE_PATH / "docs"
INSTRUCCIONES_PATH = BASE_PATH / "instruccionesArritmo"

for ruta in [DOCS_PATH, INSTRUCCIONES_PATH]:
    ruta.mkdir(parents=True, exist_ok=True)

# Cliente Chroma persistente
client = get_chroma_client()
collection = get_collection(APP_NAME)

# ============================
# 📄 CRUD Documentos
# ============================

def crear_doc(doc_id: str, texto: str):
    """Crea un nuevo documento local y lo añade a ChromaDB."""
    if not texto.strip():
        return {"error": "Texto vacío"}

    existing = collection.get(ids=[doc_id])
    if existing and existing["ids"]:
        return {"error": f"Documento {doc_id} ya existe"}

    # Guardar en Chroma y en disco
    collection.add(documents=[texto], ids=[doc_id])
    with open(DOCS_PATH / f"{doc_id}.txt", "w", encoding="utf-8") as f:
        f.write(texto)

    return {"status": "ok", "id": doc_id}


def leer_docs():
    """Lista todos los documentos locales guardados."""
    docs = []
    for archivo in DOCS_PATH.glob("*.txt"):
        with open(archivo, "r", encoding="utf-8") as f:
            docs.append({"id": archivo.stem, "texto": f.read()})
    return docs


def actualizar_doc(doc_id: str, nuevo_texto: str):
    """Actualiza el contenido de un documento existente."""
    archivo = DOCS_PATH / f"{doc_id}.txt"
    if not archivo.exists():
        return {"error": f"Documento {doc_id} no existe"}

    # Actualizar en Chroma
    collection.delete(ids=[doc_id])
    collection.add(documents=[nuevo_texto], ids=[doc_id])

    # Actualizar en disco
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(nuevo_texto)

    return {"status": "ok", "id": doc_id}


def eliminar_doc(doc_id: str):
    """Elimina un documento local y su registro en Chroma."""
    archivo = DOCS_PATH / f"{doc_id}.txt"
    if archivo.exists():
        os.remove(archivo)

    collection.delete(ids=[doc_id])
    return {"status": "ok", "id": doc_id}


# ============================
# 🧾 CRUD Instrucciones
# ============================

def crear_instruccion(nombre: str, texto: str):
    """Crea una nueva instrucción local."""
    archivo = INSTRUCCIONES_PATH / f"{nombre}.txt"
    if archivo.exists():
        return {"error": f"Instrucción {nombre} ya existe"}

    with open(archivo, "w", encoding="utf-8") as f:
        f.write(texto)

    return {"status": "ok", "nombre": nombre}


def leer_instrucciones():
    """Lista todas las instrucciones guardadas localmente."""
    instrucciones = []
    for archivo in INSTRUCCIONES_PATH.glob("*.txt"):
        with open(archivo, "r", encoding="utf-8") as f:
            instrucciones.append({"nombre": archivo.stem, "texto": f.read()})
    return instrucciones


def actualizar_instruccion(nombre: str, nuevo_texto: str):
    """Actualiza el texto de una instrucción existente."""
    archivo = INSTRUCCIONES_PATH / f"{nombre}.txt"
    if not archivo.exists():
        return {"error": f"Instrucción {nombre} no existe"}

    with open(archivo, "w", encoding="utf-8") as f:
        f.write(nuevo_texto)

    return {"status": "ok", "nombre": nombre}


def eliminar_instruccion(nombre: str):
    """Elimina una instrucción local."""
    archivo = INSTRUCCIONES_PATH / f"{nombre}.txt"
    if archivo.exists():
        os.remove(archivo)
        return {"status": "ok", "nombre": nombre}

    return {"error": f"Instrucción {nombre} no existe"}
