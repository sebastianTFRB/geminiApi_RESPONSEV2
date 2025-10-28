from fastapi import FastAPI
from routers import include_app_routers

app = FastAPI()

# Montamos las rutas de los 3 módulos
include_app_routers(app)
