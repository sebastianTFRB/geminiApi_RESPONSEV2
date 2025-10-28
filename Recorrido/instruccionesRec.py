from pathlib import Path
from pypdf import PdfReader

def cargar_instrucciones(ruta: Path):
    """
    Carga instrucciones desde la carpeta especificada.
    Acepta archivos .txt, .md y .pdf
    """
    ruta.mkdir(exist_ok=True)

    textos = []
    for file in ruta.glob("**/*"):
        if file.suffix.lower() in [".txt", ".md"]:
            with open(file, "r", encoding="utf-8") as f:
                textos.append(f.read())

        elif file.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(file)
                for page in reader.pages:
                    textos.append(page.extract_text() or "")
            except Exception as e:
                print(f"⚠️ Error leyendo {file.name}: {e}")

    instrucciones = "\n".join(textos)
    print(f"✅ Instrucciones cargadas desde {ruta} ({len(textos)} archivos)")
    return instrucciones
