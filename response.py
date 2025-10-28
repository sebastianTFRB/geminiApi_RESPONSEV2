import requests
import base64

# 1. Hacemos la petición a nuestra API
url = "http://127.0.0.1:8000/chat"
payload = {"pregunta": "hablame de arritmias cardicas"}
res = requests.post(url, json=payload)

data = res.json()

# 2. Guardamos el audio en un archivo MP3
audio_base64 = data["audio"]
audio_bytes = base64.b64decode(audio_base64)

with open("respuesta.wav", "wb") as f:
    f.write(audio_bytes)

print("✅ Texto:", data["respuesta"])
print("🎧 Audio guardado en 'respuesta.mp3'")
