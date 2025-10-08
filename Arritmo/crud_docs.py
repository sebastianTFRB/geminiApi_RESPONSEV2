# crud_docs.py
import os
import json
import chromadb
from pathlib import Path

# Configuración
APP_NAME = "Arritmo"

# Inicializar ChromaDB
chroma = chromadb.Client()
collection = chroma.get_or_create_collection(f"{APP_NAME}_docs")

# Rutas de carpetas
DOCS_PATH = Path(f"./{APP_NAME}/docs")
DOCS_PATH.mkdir(parents=True, exist_ok=True)

INSTRUCCIONES_PATH = Path(f"./{APP_NAME}/instruccionesArritmo")
INSTRUCCIONES_PATH.mkdir(parents=True, exist_ok=True)


# ---------------------------
# 📌 CRUD para Documentos
# ---------------------------
def crear_doc(doc_id: str, texto: str):
    if not texto.strip():
        return {"error": "Texto vacío"}

    existing = collection.get(ids=[doc_id])
    if existing["ids"]:
        return {"error": f"Documento {doc_id} ya existe"}

    # Guardar en Chroma y archivo local
    collection.add(documents=[texto], ids=[doc_id])
    with open(DOCS_PATH / f"{doc_id}.txt", "w", encoding="utf-8") as f:
        f.write(texto)
    return {"status": "ok", "id": doc_id}


def leer_docs():
    """Lista todos los documentos locales"""
    docs = []
    for archivo in DOCS_PATH.glob("*.txt"):
        with open(archivo, "r", encoding="utf-8") as f:
            docs.append({"id": archivo.stem, "texto": f.read()})
    return docs


def actualizar_doc(doc_id: str, nuevo_texto: str):
    archivo = DOCS_PATH / f"{doc_id}.txt"
    if not archivo.exists():
        return {"error": f"Documento {doc_id} no existe"}

    # Actualizar en Chroma
    collection.delete(ids=[doc_id])
    collection.add(documents=[nuevo_texto], ids=[doc_id])

    # Reescribir archivo
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(nuevo_texto)
    return {"status": "ok", "id": doc_id}


def eliminar_doc(doc_id: str):
    archivo = DOCS_PATH / f"{doc_id}.txt"
    if archivo.exists():
        os.remove(archivo)

    collection.delete(ids=[doc_id])
    return {"status": "ok", "id": doc_id}


# ---------------------------
# 📌 CRUD para Instrucciones
# ---------------------------
def crear_instruccion(nombre: str, texto: str):
    archivo = INSTRUCCIONES_PATH / f"{nombre}.txt"
    if archivo.exists():
        return {"error": f"Instrucción {nombre} ya existe"}
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(texto)
    return {"status": "ok", "nombre": nombre}


def leer_instrucciones():
    instrucciones = []
    for archivo in INSTRUCCIONES_PATH.glob("*.txt"):
        with open(archivo, "r", encoding="utf-8") as f:
            instrucciones.append({"nombre": archivo.stem, "texto": f.read()})
    return instrucciones


def actualizar_instruccion(nombre: str, nuevo_texto: str):
    archivo = INSTRUCCIONES_PATH / f"{nombre}.txt"
    if not archivo.exists():
        return {"error": f"Instrucción {nombre} no existe"}
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(nuevo_texto)
    return {"status": "ok", "nombre": nombre}


def eliminar_instruccion(nombre: str):
    archivo = INSTRUCCIONES_PATH / f"{nombre}.txt"
    if archivo.exists():
        os.remove(archivo)
        return {"status": "ok", "nombre": nombre}
    return {"error": f"Instrucción {nombre} no existe"}
