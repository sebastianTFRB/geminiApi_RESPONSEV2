# InteligenSchool/crud_profiles.py
from google.cloud import firestore
from pathlib import Path
from chroma_manager import get_collection
import os

# Inicializar Firestore
db = firestore.Client()

APP_NAME = os.getenv("APP_NAME", "InteligenSchool")
BASE_PATH = Path(f"./{APP_NAME}")
BASE_PATH.mkdir(parents=True, exist_ok=True)

# collection desde manager
collection = get_collection("InteligenSchool")

def save_student_profile(student_id: str, profile: dict):
    db.collection("student_profiles").document(student_id).set(profile)
    doc_id = f"student_profile:{student_id}"
    parts = []
    if profile.get("gustos"):
        parts.append("Gustos: " + ", ".join(profile.get("gustos", [])))
    if profile.get("debilidades"):
        parts.append("Debilidades: " + ", ".join(profile.get("debilidades", [])))
    if profile.get("notas"):
        parts.append("Notas: " + profile.get("notas"))
    text = "\n".join(parts) if parts else "Perfil vacío."
    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass
    collection.add(
        documents=[text],
        ids=[doc_id],
        metadatas=[{"tipo": "student_profile", "studentId": student_id}],
    )
    return {"status": "ok"}

def get_student_profile(student_id: str):
    doc = db.collection("student_profiles").document(student_id).get()
    if doc.exists:
        return doc.to_dict()
    return {"error": "no existe"}

def delete_student_profile(student_id: str):
    db.collection("student_profiles").document(student_id).delete()
    try:
        collection.delete(ids=[f"student_profile:{student_id}"])
    except Exception:
        pass
    return {"status": "ok"}
