from fastapi import FastAPI
from Arritmo.routes import router as arritmo_router
from Recorrido.routes import router as recorrido_router
from InteligenSchool.routes import router as inteligens_router

def include_app_routers(app: FastAPI):
    app.include_router(arritmo_router, prefix="/arritmo", tags=["arritmo"])
    app.include_router(recorrido_router, prefix="/recorrido", tags=["recorrido"])
    app.include_router(inteligens_router, prefix="/inteligen", tags=["inteligensSchool"])
