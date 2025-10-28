import os
from pathlib import Path
from chroma_manager import get_collection  # ✅ usamos el singleton global

# ==============================
# CONFIGURACIÓN GENERAL
# ==============================
APP_NAME = os.getenv("APP_NAME", "InteligenSchool")

BASE_PATH = Path(f"./{APP_NAME}")
DOCS_PATH = BASE_PATH / "docs"
INSTRUCCIONES_DIR = BASE_PATH / "instrucciones_materia"
CHROMA_PATH = BASE_PATH / ".chromadb"

# Crear carpetas necesarias
for path in [DOCS_PATH, INSTRUCCIONES_DIR, CHROMA_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# ==============================
# CLIENTE CHROMA (SINGLETON)
# ==============================
collection = get_collection(APP_NAME)  # ✅ misma instancia compartida

# ==============================
# CRUD DOCUMENTOS (GENERALES)
# ==============================
def crear_doc(
    doc_id: str,
    texto: str,
    tipo: str = "materia_doc",
    materia_id: str | None = None,
    grupo_id: str | None = None,
    student_id: str | None = None,
):
    if not texto.strip():
        return {"error": "Texto vacío"}

    try:
        existing = collection.get(ids=[doc_id])
        if existing and existing.get("ids") and existing["ids"][0]:
            return {"error": f"Documento {doc_id} ya existe"}
    except Exception:
        pass

    metadata = {"tipo": tipo}
    if materia_id:
        metadata["materiaId"] = materia_id
    if grupo_id:
        metadata["grupoId"] = grupo_id
    if student_id:
        metadata["studentId"] = student_id

    collection.add(documents=[texto], ids=[doc_id], metadatas=[metadata])
    (DOCS_PATH / f"{doc_id}.txt").write_text(texto, encoding="utf-8")

    return {"status": "ok", "id": doc_id}


def leer_docs():
    docs = []
    for archivo in DOCS_PATH.glob("*.txt"):
        texto = archivo.read_text(encoding="utf-8")
        docs.append({"id": archivo.stem, "texto": texto})
    return docs


def actualizar_doc(doc_id: str, nuevo_texto: str):
    archivo = DOCS_PATH / f"{doc_id}.txt"
    if not archivo.exists():
        return {"error": f"Documento {doc_id} no existe"}

    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass

    collection.add(documents=[nuevo_texto], ids=[doc_id])
    archivo.write_text(nuevo_texto, encoding="utf-8")
    return {"status": "ok", "id": doc_id}


def eliminar_doc(doc_id: str):
    archivo = DOCS_PATH / f"{doc_id}.txt"
    if archivo.exists():
        archivo.unlink()
    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass
    return {"status": "ok", "id": doc_id}


# ==============================
# CRUD INSTRUCCIONES POR MATERIA
# ==============================
def crear_instruccion(materia_id: str, texto: str):
    archivo = INSTRUCCIONES_DIR / f"{materia_id}.txt"
    if archivo.exists():
        return {"error": "Ya existe instrucción para esta materia"}
    archivo.write_text(texto, encoding="utf-8")
    return {"status": "ok", "materiaId": materia_id}


def leer_instruccion(materia_id: str):
    archivo = INSTRUCCIONES_DIR / f"{materia_id}.txt"
    if not archivo.exists():
        return {"error": "No existe instrucción"}
    return {"materiaId": materia_id, "texto": archivo.read_text(encoding="utf-8")}


def actualizar_instruccion(materia_id: str, texto: str):
    archivo = INSTRUCCIONES_DIR / f"{materia_id}.txt"
    archivo.write_text(texto, encoding="utf-8")
    return {"status": "ok", "materiaId": materia_id}


def eliminar_instruccion(materia_id: str):
    archivo = INSTRUCCIONES_DIR / f"{materia_id}.txt"
    if archivo.exists():
        archivo.unlink()
        return {"status": "ok", "materiaId": materia_id}
    return {"error": "No existe instrucción"}
