import os
import sys

from groq import Groq
from openai import OpenAI
import google.generativeai as genai

# Chaves extraídas do .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def test_groq():
    print("\n--- Testando GROQ ---")
    try:
        client = Groq(api_key=GROQ_API_KEY)
        models = client.models.list()
        print("✅ Conectado com sucesso.")
        print("Modelos disponíveis (Top 3):")
        for m in sorted(models.data, key=lambda x: x.id)[:3]:
            print(f"  - {m.id}")
        return True
    except Exception as e:
        print(f"❌ Falha no Groq: {e}")
        return False

def test_nvidia():
    print("\n--- Testando NVIDIA ---")
    try:
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=NVIDIA_API_KEY
        )
        models = client.models.list()
        print("✅ Conectado com sucesso.")
        print("Modelos disponíveis (Top 3):")
        for m in sorted(models.data, key=lambda x: x.id)[:3]:
            print(f"  - {m.id}")
        return True
    except Exception as e:
        print(f"❌ Falha na Nvidia: {e}")
        return False

def test_gemini():
    print("\n--- Testando GEMINI ---")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print("✅ Conectado com sucesso.")
        print("Modelos disponíveis (Top 3):")
        for m in models[:3]:
            print(f"  - {m}")
        return True
    except Exception as e:
        print(f"❌ Falha no Gemini: {e}")
        return False

if __name__ == "__main__":
    test_groq()
    test_nvidia()
    test_gemini()
