import requests, re, json
import chromadb
from pathlib import Path
from .instruccionesRec import cargar_instrucciones

# Configuración
APP_NAME = "Recorrido"
GEMINI_KEY = "AIzaSyAdvIae-CvrEiOMkMgjjRusV_tixeFGbfc"
MODELO_GEMINI = "gemini-2.0-flash"  # Modelo disponible más reciente

# Inicializar ChromaDB colección propia
chroma = chromadb.Client()
collection = chroma.get_or_create_collection(f"{APP_NAME}_docs")

# Carpeta de documentos
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

def insertar_doc(doc):
    if not doc.texto.strip():
        return {"error": "Texto vacío"}
    existing = collection.get(ids=[doc.id])
    if existing['ids']:
        return {"error": f"Documento {doc.id} ya existe"}
    collection.add(documents=[doc.texto], ids=[doc.id])
    with open(DOCS_PATH / f"{doc.id}.txt", "w", encoding="utf-8") as f:
        f.write(doc.texto)
    return {"status": "ok", "id": doc.id}

def set_nodo_actual(nodo_id: str):
    global NODO_ACTUAL, NODOS
    NODOS = cargar_nodos()  # recarga por si el archivo cambió

    # Caso 1: nodo_id es vacío o None → fallback
    if not nodo_id:
        NODO_ACTUAL = "nodo_sin_contexto"
        return {"status": "ok", "nodo": NODO_ACTUAL, "info": "Asignado automáticamente por falta de id"}

    # Caso 2: nodo_id existe en nodos.json
    if nodo_id in NODOS:
        NODO_ACTUAL = nodo_id
        return {"status": "ok", "nodo": nodo_id}

    # Caso 3: nodo_id no existe → fallback también
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
    # Recargar nodos (para reflejar cambios en caliente)
    global NODOS
    NODOS = cargar_nodos()

    # Recuperar contexto desde Chroma
    resultados = collection.query(query_texts=[data.pregunta], n_results=3)
    contexto = " ".join(resultados["documents"][0]) if resultados["documents"] else ""

    # Contexto del nodo actual
    nodo_info = NODOS.get(NODO_ACTUAL, "")

    # Construir prompt incluyendo info del nodo
    prompt = (
        f"Instrucciones del sistema ({APP_NAME}):\n{INSTRUCCIONES}\n\n"
        f"Contexto recuperado:\n{contexto}\n\n"
        f"Información relevante del lugar actual (usar como referencia, no repetir literalmente):\n{nodo_info}\n\n"
        f"Pregunta del usuario: {data.pregunta}\n\n"
        f"Nota para el modelo: Usa la información del lugar actual para dar respuestas más precisas y contextuales, "
        f"pero no repitas exactamente la descripción proporcionada."
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

    return {"respuesta": respuesta, "audio": audio_data, "contexto": contexto}

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
