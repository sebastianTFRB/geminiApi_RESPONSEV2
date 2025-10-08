from fastapi import APIRouter
from pydantic import BaseModel
from .logicnodes import responder_chat, stt_transcripcion, set_nodo_actual, get_nodo_actual
from .crud_docs import (
    crear_doc, leer_docs, actualizar_doc, eliminar_doc,
    crear_instruccion, leer_instrucciones, actualizar_instruccion, eliminar_instruccion
)


router = APIRouter()

class Pregunta(BaseModel):
    pregunta: str

class AudioData(BaseModel):
    audio: str


class Nodo(BaseModel):
    nodo: str   
    
class Documento(BaseModel):
    id: str
    texto: str

class Instruccion(BaseModel):
    nombre: str
    texto: str


@router.post("/chat")
def chat(data: Pregunta):
    return responder_chat(data)

@router.post("/stt")
def stt(data: AudioData):
    return stt_transcripcion(data)


@router.post("/nodo")
def actualizar_nodo(data: Nodo):
    return set_nodo_actual(data.nodo)

@router.get("/nodo_actual")
def nodo_actual():
    return get_nodo_actual()




@router.post("/docs")
def crear_documento(doc: Documento):
    return crear_doc(doc.id, doc.texto)

@router.get("/docs")
def listar_documentos():
    return leer_docs()

@router.put("/docs/{doc_id}")
def actualizar_documento(doc_id: str, doc: Documento):
    return actualizar_doc(doc_id, doc.texto)

@router.delete("/docs/{doc_id}")
def eliminar_documento(doc_id: str):
    return eliminar_doc(doc_id)




@router.post("/instrucciones")
def crear_instr(instr: Instruccion):
    return crear_instruccion(instr.nombre, instr.texto)

@router.get("/instrucciones")
def listar_instrucciones():
    return leer_instrucciones()

@router.put("/instrucciones/{nombre}")
def actualizar_instr(nombre: str, instr: Instruccion):
    return actualizar_instruccion(nombre, instr.texto)

@router.delete("/instrucciones/{nombre}")
def eliminar_instr(nombre: str):
    return eliminar_instruccion(nombre)
