from fastapi import APIRouter
from pydantic import BaseModel
from .logic import insertar_doc, responder_chat, stt_transcripcion

router = APIRouter()

class Pregunta(BaseModel):
    pregunta: str

class AudioData(BaseModel):
    audio: str

class Documento(BaseModel):
    id: str
    texto: str

@router.post("/insertar")
def insertar(doc: Documento):
    return insertar_doc(doc)

@router.post("/chat")
def chat(data: Pregunta):
    return responder_chat(data)

@router.post("/stt")
def stt(data: AudioData):
    return stt_transcripcion(data)
