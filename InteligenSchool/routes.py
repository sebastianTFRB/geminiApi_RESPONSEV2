# InteligenSchool/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .logic import insertar_doc_chroma, responder_chat
from .crud_docs import crear_doc, leer_docs, actualizar_doc, eliminar_doc, crear_instruccion, leer_instruccion, actualizar_instruccion, eliminar_instruccion
from .crud_profiles import save_student_profile, get_student_profile, delete_student_profile

router = APIRouter()

# Models
class ChatRequest(BaseModel):
    pregunta: str
    materiaId: str | None = None
    estudianteId: str | None = None

class Documento(BaseModel):
    id: str
    texto: str
    tipo: str | None = "materia_doc"
    materiaId: str | None = None
    grupoId: str | None = None
    studentId: str | None = None

class ProfileBody(BaseModel):
    gustos: list[str] | None = None
    debilidades: list[str] | None = None
    notas: str | None = None

# Chat endpoint (extendido)
@router.post("/chat")
def chat(body: ChatRequest):
    return responder_chat(body)

# Docs endpoints (uses crud_docs)
@router.post("/docs")
def create_doc(doc: Documento):
    return crear_doc(doc.id, doc.texto)  # for CRUD you can call crear_doc with metadata wrapper if needed

@router.get("/docs")
def list_docs():
    return leer_docs()

@router.put("/docs/{doc_id}")
def update_doc(doc_id: str, doc: Documento):
    return actualizar_doc(doc_id, doc.texto)

@router.delete("/docs/{doc_id}")
def delete_doc(doc_id: str):
    return eliminar_doc(doc_id)

# Instrucciones por materia
@router.post("/materias/{materia_id}/instruccion")
def create_instr(materia_id: str, body: dict):
    return crear_instruccion(materia_id, body.get("texto",""))

@router.get("/materias/{materia_id}/instruccion")
def get_instr(materia_id: str):
    return leer_instruccion(materia_id)

@router.put("/materias/{materia_id}/instruccion")
def put_instr(materia_id: str, body: dict):
    return actualizar_instruccion(materia_id, body.get("texto",""))

@router.delete("/materias/{materia_id}/instruccion")
def del_instr(materia_id: str):
    return eliminar_instruccion(materia_id)

# Student profile endpoints
@router.post("/students/{student_id}/profile")
def post_profile(student_id: str, body: ProfileBody):
    return save_student_profile(student_id, body.dict())

@router.get("/students/{student_id}/profile")
def get_profile(student_id: str):
    return get_student_profile(student_id)

@router.delete("/students/{student_id}/profile")
def delete_profile(student_id: str):
    return delete_student_profile(student_id)
