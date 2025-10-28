import requests, re
from pathlib import Path
from .instruccionesAr import cargar_instrucciones
from chroma_manager import get_collection, get_chroma_client

# Configuración
APP_NAME = "Arritmo"
GEMINI_KEY = "AIzaSyAdvIae-CvrEiOMkMgjjRusV_tixeFGbfc"
MODELO_GEMINI = "gemini-2.0-flash"

# Inicializar ChromaDB colección propia
collection = get_collection(APP_NAME)
client = get_chroma_client()

# Carpeta de documentos
DOCS_PATH = Path(f"./{APP_NAME}/docs")
DOCS_PATH.mkdir(parents=True, exist_ok=True)

# Cargar instrucciones propias
INSTRUCCIONES_PATH = Path(f"./{APP_NAME}/instruccionesArritmo")
INSTRUCCIONES = cargar_instrucciones(INSTRUCCIONES_PATH)


# =============================
# 🔧 Funciones utilitarias
# =============================

def limpiar_texto(texto: str) -> str:
    texto = re.sub(r"[*#_`]+", "", texto)
    return texto.replace("\n", " ").strip()


# =============================
# 📂 Gestión de documentos
# =============================

def recargar_datos():
    """
    Recarga tanto las instrucciones como todos los documentos de la carpeta DOCS_PATH
    en la colección ChromaDB.
    """
    global INSTRUCCIONES, collection

    # Recargar instrucciones
    INSTRUCCIONES = cargar_instrucciones(INSTRUCCIONES_PATH)

    # Eliminar y recrear colección desde cliente global
    client.delete_collection(f"{APP_NAME}_docs")
    collection = client.get_or_create_collection(f"{APP_NAME}_docs")

    # Recargar documentos locales
    for doc_path in DOCS_PATH.glob("*.txt"):
        with open(doc_path, encoding="utf-8") as f:
            texto = f.read().strip()
        if texto:
            collection.add(documents=[texto], ids=[doc_path.stem])

    return {"status": "recargado", "docs": len(list(DOCS_PATH.glob('*.txt')))}


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


# =============================
# 💬 Chat + Gemini + TTS
# =============================

def responder_chat(data):
    # Recuperar contexto desde Chroma
    resultados = collection.query(query_texts=[data.pregunta], n_results=3)
    contexto = " ".join(resultados["documents"][0]) if resultados["documents"] else ""

    # Construir prompt
    prompt = (
        f"Instrucciones del sistema ({APP_NAME}):\n{INSTRUCCIONES}\n\n"
        f"Contexto recuperado:\n{contexto}\n\n"
        f"Pregunta del usuario: {data.pregunta}"
    )

    # Llamada a Gemini
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


# =============================
# 🎙️ STT (voz a texto)
# =============================

def stt_transcripcion(data):
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
