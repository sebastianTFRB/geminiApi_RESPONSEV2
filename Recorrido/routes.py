from fastapi import APIRouter
from pydantic import BaseModel
from .logicnodes import responder_chat, stt_transcripcion, set_nodo_actual

router = APIRouter()

class Pregunta(BaseModel):
    pregunta: str

class AudioData(BaseModel):
    audio: str

class Documento(BaseModel):
    id: str
    texto: str

class Nodo(BaseModel):
    nodo: str   

@router.post("/insertar")
def insertar(doc: Documento):
    return insertar_doc(doc)

@router.post("/chat")
def chat(data: Pregunta):
    return responder_chat(data)

@router.post("/stt")
def stt(data: AudioData):
    return stt_transcripcion(data)


@router.post("/nodo")
def actualizar_nodo(data: Nodo):
    return set_nodo_actual(data.nodo)
