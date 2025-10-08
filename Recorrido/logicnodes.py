import requests, re, json
from pathlib import Path
from .instruccionesRec import cargar_instrucciones

# Configuración
APP_NAME = "Recorrido"
GEMINI_KEY = "AIzaSyAdvIae-CvrEiOMkMgjjRusV_tixeFGbfc"
MODELO_GEMINI = "gemini-2.0-flash"  # Modelo disponible más reciente

# Carpeta de documentos (contexto local)
DOCS_PATH = Path(f"./{APP_NAME}/docs")
DOCS_PATH.mkdir(parents=True, exist_ok=True)

# Archivo de nodos (contextos por lugar)
NODOS_PATH = Path(f"./{APP_NAME}/nodos.json")

def cargar_nodos():
    if NODOS_PATH.exists():
        with open(NODOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Nodo actual del usuario (ejemplo simple global)
NODOS = cargar_nodos()
NODO_ACTUAL = "auditorio"

# Cargar instrucciones propias
INSTRUCCIONES = cargar_instrucciones(Path(f"./{APP_NAME}/instruccionesRecorrido"))

def limpiar_texto(texto: str) -> str:
    texto = re.sub(r"[*#_`]+", "", texto)
    return texto.replace("\n", " ").strip()

def cargar_docs():
    """Carga todos los documentos de DOCS_PATH y los devuelve como lista de strings"""
    docs = []
    for archivo in DOCS_PATH.glob("*.txt"):
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if contenido:
                docs.append(contenido)
    return docs

def get_nodo_actual():
    global NODO_ACTUAL, NODOS
    NODOS = cargar_nodos()
    return {
        "status": "ok",
        "nodo_actual": NODO_ACTUAL,
        "info": NODOS.get(NODO_ACTUAL, "Nodo no encontrado")
    }


def set_nodo_actual(nodo_id: str):
    global NODO_ACTUAL, NODOS
    NODOS = cargar_nodos()  # recarga por si el archivo cambió

    if not nodo_id:
        NODO_ACTUAL = "nodo_sin_contexto"
        return {"status": "ok", "nodo": NODO_ACTUAL, "info": "Asignado automáticamente por falta de id"}

    if nodo_id in NODOS:
        NODO_ACTUAL = nodo_id
        return {"status": "ok", "nodo": nodo_id}

    NODO_ACTUAL = "nodo_sin_contexto"
    return {
        "status": "warning",
        "nodo": NODO_ACTUAL,
        "info": f"El nodo '{nodo_id}' no fue encontrado. Se asignó 'nodo_sin_contexto'."
    }

def responder_chat(data):
    """
    data: objeto con atributo `pregunta`
    """
    global NODOS
    NODOS = cargar_nodos()

    # Recuperar contexto desde archivos locales
    documentos = cargar_docs()

    # Formatear documentos como lista Markdown para darles más peso
    contexto_formateado = "\n\n".join([f"- {doc}" for doc in documentos])

    # Contexto del nodo actual
    nodo_info = NODOS.get(NODO_ACTUAL, "")

    # Construir prompt
    prompt = (
        f"Instrucciones del sistema ({APP_NAME}):\n{INSTRUCCIONES}\n\n"
        f"Contexto recuperado (usar este contenido como referencia principal para responder):\n{contexto_formateado}\n\n"
        f"Información relevante del lugar actual (usar solo si la pregunta lo requiere):\n"
        f"{nodo_info if 'lugar' in data.pregunta.lower() else ''}\n\n"
        f"Pregunta del usuario: {data.pregunta}\n\n"
        f"Nota para el modelo:\n"
        f"- Prioriza siempre usar la información de los documentos recuperados.\n"
        f"- Usa la información del lugar donde esta cuando te lo pida.\n"
        f"- Responde de manera concisa, solo amplía si el usuario pide más detalles.\n"
    )

    # Endpoint Gemini
    url_chat = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_GEMINI}:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.7}
    }

    r = requests.post(url_chat, json=payload)
    r.raise_for_status()
    chat_data = r.json()
    respuesta = chat_data["candidates"][0]["content"]["parts"][0]["text"]
    respuesta_limpia = limpiar_texto(respuesta)

    # TTS
    url_tts = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GEMINI_KEY}"
    tts_payload = {
        "input": {"text": respuesta_limpia},
        "voice": {"languageCode": "es-ES", "name": "es-ES-Neural2-B"},
        "audioConfig": {"audioEncoding": "LINEAR16"}
    }
    r2 = requests.post(url_tts, json=tts_payload)
    r2.raise_for_status()
    audio_data = r2.json()["audioContent"]

    return {"respuesta": respuesta, "audio": audio_data, "contexto": contexto_formateado}

def stt_transcripcion(data):
    """
    Transcribe audio a texto usando STT de Google.
    """
    url_stt = f"https://speech.googleapis.com/v1/speech:recognize?key={GEMINI_KEY}"
    payload = {
        "config": {"encoding": "LINEAR16", "sampleRateHertz": 16000, "languageCode": "es-ES"},
        "audio": {"content": data.audio}
    }
    r = requests.post(url_stt, json=payload)
    r.raise_for_status()
    result = r.json()
    texto = result.get("results", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
    return {"texto": texto}
