import os
import re
import requests
from pathlib import Path
from google.cloud import firestore
from chroma_manager import get_collection  # ✅ un solo cliente global

# ============================
# CONFIGURACIÓN GENERAL
# ============================
APP_NAME = "InteligenSchool"
GEMINI_KEY = "AIzaSyAdvIae-CvrEiOMkMgjjRusV_tixeFGbfc"
MODELO_GEMINI = "gemini-2.0-flash"

# Configura la ruta del archivo de credenciales de Firestore
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    "/Users/josemixta/Desktop/geminiApi_RESPONSEV2/InteligenSchool/MIT/inteligence-companya.json"
)

# Inicializa Firestore
db = firestore.Client()

# ============================
# CONFIGURACIÓN DE CHROMADB
# ============================
collection = get_collection(APP_NAME)  # ✅ usa el mismo singleton global

# ============================
# ESTRUCTURA DE CARPETAS LOCALES
# ============================
BASE_PATH = Path(f"./{APP_NAME}")
DOCS_PATH = BASE_PATH / "docs"
INSTRUCCIONES_MATERIA_PATH = BASE_PATH / "instrucciones_materia"
INSTRUCCIONES_MATERIA_PATH.mkdir(parents=True, exist_ok=True)
DOCS_PATH.mkdir(parents=True, exist_ok=True)

# ============================
# CARGA DE INSTRUCCIONES GLOBALES
# ============================
GLOBAL_INSTRUCCIONES_FILE = BASE_PATH / "instruccionesInteligensSchool" / "global.txt"
GLOBAL_INSTRUCCIONES_FILE.parent.mkdir(parents=True, exist_ok=True)

INSTRUCCIONES_GLOBAL = ""
if GLOBAL_INSTRUCCIONES_FILE.exists():
    INSTRUCCIONES_GLOBAL = GLOBAL_INSTRUCCIONES_FILE.read_text(encoding="utf-8")

# ============================
# FUNCIONES AUXILIARES
# ============================
def limpiar_texto(texto: str) -> str:
    texto = re.sub(r"[*#_`]+", "", texto)
    return texto.replace("\n", " ").strip()


# -----------------------
# CRUD / CHROMA HELPERS
# -----------------------
def insertar_doc_chroma(doc_id: str, texto: str, metadata: dict | None = None):
    if not texto or not texto.strip():
        return {"error": "Texto vacío"}

    try:
        existing = collection.get(ids=[doc_id])
        if existing and existing.get("ids") and existing["ids"][0]:
            return {"error": f"Documento {doc_id} ya existe"}
    except Exception:
        pass

    meta = metadata or {}
    collection.add(documents=[texto], ids=[doc_id], metadatas=[meta])
    with open(DOCS_PATH / f"{doc_id}.txt", "w", encoding="utf-8") as f:
        f.write(texto)
    return {"status": "ok", "id": doc_id}


def delete_doc_chroma(doc_id: str):
    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass
    f = DOCS_PATH / f"{doc_id}.txt"
    if f.exists():
        f.unlink()
    return {"status": "ok", "id": doc_id}


# -----------------------
# STUDENT PROFILE HELPERS
# -----------------------
def read_student_profile(student_id: str) -> dict | None:
    doc = db.collection("student_profiles").document(student_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def save_student_profile(student_id: str, profile: dict):
    db.collection("student_profiles").document(student_id).set(profile)
    doc_id = f"student_profile:{student_id}"

    summary_parts = []
    if profile.get("gustos"):
        summary_parts.append("Gustos: " + ", ".join(profile.get("gustos", [])))
    if profile.get("debilidades"):
        summary_parts.append("Debilidades: " + ", ".join(profile.get("debilidades", [])))
    if profile.get("notas"):
        summary_parts.append("Notas: " + profile.get("notas"))

    summary_text = "\n".join(summary_parts) if summary_parts else "Perfil vacío."

    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass

    collection.add(
        documents=[summary_text],
        ids=[doc_id],
        metadatas=[{"tipo": "student_profile", "studentId": student_id}],
    )
    return {"status": "ok"}


def delete_student_profile(student_id: str):
    db.collection("student_profiles").document(student_id).delete()
    try:
        collection.delete(ids=[f"student_profile:{student_id}"])
    except Exception:
        pass
    return {"status": "ok"}


# -----------------------
# RAG / CHATBOT
# -----------------------
def _query_chroma_filtered(pregunta: str, n: int = 3, where: dict | None = None):
    try:
        if where:
            return collection.query(query_texts=[pregunta], n_results=n, where=where)
        else:
            return collection.query(query_texts=[pregunta], n_results=n)
    except TypeError:
        return collection.query(query_texts=[pregunta], n_results=n)
    except Exception as e:
        print("Chroma query error:", e)
        return {"documents": [[]], "ids": [[]], "metadatas": [[]]}


def responder_chat(body):
    pregunta = getattr(body, "pregunta", "") or ""
    materia_id = getattr(body, "materiaId", None)
    estudiante_id = getattr(body, "estudianteId", None)

    pregunta = pregunta.strip()
    if not pregunta:
        return {"error": "Pregunta vacía"}

    instrucciones_global = INSTRUCCIONES_GLOBAL
    instrucciones_materia = ""
    if materia_id:
        f = INSTRUCCIONES_MATERIA_PATH / f"{materia_id}.txt"
        if f.exists():
            instrucciones_materia = f.read_text(encoding="utf-8")

    perfil_text = ""
    if estudiante_id:
        perfil = read_student_profile(estudiante_id)
        if perfil:
            parts = []
            if perfil.get("gustos"):
                parts.append("Gustos: " + ", ".join(perfil.get("gustos", [])))
            if perfil.get("debilidades"):
                parts.append("Debilidades: " + ", ".join(perfil.get("debilidades", [])))
            if perfil.get("notas"):
                parts.append("Notas: " + perfil.get("notas"))
            perfil_text = "\n".join(parts)

    docs_texts, sources = [], []

    if materia_id:
        r = _query_chroma_filtered(pregunta, n=3, where={"materiaId": materia_id})
        docs = r.get("documents", [[]])[0]
        ids = r.get("ids", [[]])[0]
        for i, d in enumerate(docs):
            if d:
                docs_texts.append(d)
                sources.append(ids[i] if i < len(ids) else None)

    if estudiante_id:
        r = _query_chroma_filtered(pregunta, n=2, where={"studentId": estudiante_id})
        docs = r.get("documents", [[]])[0]
        ids = r.get("ids", [[]])[0]
        for i, d in enumerate(docs):
            if d:
                docs_texts.append(d)
                sources.append(ids[i] if i < len(ids) else None)

    r = _query_chroma_filtered(pregunta, n=3, where={"tipo": "global"})
    docs = r.get("documents", [[]])[0]
    ids = r.get("ids", [[]])[0]
    for i, d in enumerate(docs):
        if d:
            docs_texts.append(d)
            sources.append(ids[i] if i < len(ids) else None)

    contexto = "\n\n".join(docs_texts[:6])

    prompt = (
        f"Instrucciones globales:\n{instrucciones_global}\n\n"
        f"Instrucciones materia:\n{instrucciones_materia}\n\n"
        f"Perfil estudiante:\n{perfil_text}\n\n"
        f"Contexto recuperado:\n{contexto}\n\n"
        f"Pregunta: {pregunta}\n\n"
        "Responde de forma clara y breve. Si usas información de documentos, indica la fuente (id)."
    )

    url_chat = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODELO_GEMINI}:generateContent?key={GEMINI_KEY}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 350, "temperature": 0.2},
    }

    resp = requests.post(url_chat, json=payload)
    resp.raise_for_status()
    chat_data = resp.json()

    try:
        respuesta = chat_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        respuesta = str(chat_data)

    respuesta = limpiar_texto(respuesta)

    return {"respuesta": respuesta, "contexto": contexto, "sources": [s for s in sources if s]}
