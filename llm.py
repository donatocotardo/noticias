import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODELO = os.environ["GEMINI_MODEL"]
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def generar_json(prompt: str, reintentos: int = 3) -> str:
    """Envía el prompt y devuelve el texto de la respuesta (esperamos JSON)."""
    ultimo_error = None
    for intento in range(reintentos):
        try:
            r = _client.models.generate_content(
                model=MODELO,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            return r.text
        except Exception as e:
            ultimo_error = e
            print(f"[llm] intento {intento + 1} fallido: {e}")
            time.sleep(10 * (intento + 1))
    raise RuntimeError(f"El LLM falló tras {reintentos} intentos: {ultimo_error}")