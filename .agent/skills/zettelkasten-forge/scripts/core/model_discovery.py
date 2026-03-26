"""
Model Discovery Module (Zettelkasten Forge)
Descobre dinamicamente os modelos disponíveis nas APIs (Groq, Nvidia, Gemini)
Aplicando filtros de capacidade de contexto (>= 125k) e versão (Gemini >= 2.0).
Gera uma Fila Mágica de Fallback, eliminando modelos hardcoded.
"""
import json
import logging
import urllib.request
import urllib.error
from . import config

logger = logging.getLogger("model_discovery")

# Cache em memória para não martelar as APIs de listagem de modelos a cada log processado
_FALLBACK_QUEUE_CACHE: list[dict] = []

def _fetch_json(url: str, headers: dict = None) -> dict:
    all_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if headers:
        all_headers.update(headers)
        
    req = urllib.request.Request(url, headers=all_headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.warning("Falha ao consultar modelos em %s: %s", url, str(e))
        return {}


def get_groq_models() -> list[str]:
    """Busca modelos na Groq, priorizando contexto >= 125k e famílias inteligentes (Llama 3.3, DeepSeek, Mixtral)."""
    if not config.GROQ_API_KEY:
        return []

    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}
    data = _fetch_json(url, headers)

    valid_models = []
    # Heurística atual da Groq para modelos robustos de 128k+
    for model in data.get("data", []):
        name = model.get("id", "").lower()
        cw = model.get("context_window", 0)
        
        # Filtro: Contexto >= 125k E famílias de alta inteligência
        if cw >= 125000:
            # Famílias aceitas: Llama 70b+, DeepSeek, Mixtral 8x22b, Qwen
            if any(tech in name for tech in ["70b", "deepseek", "mixtral", "qwen", "llama-3.3"]):
                valid_models.append(name)
            
    # Ordem de preferência: Llama 3.3/3.1 primeiro, depois DeepSeek, depois outros
    valid_models.sort(key=lambda x: (
        "3.3" not in x, 
        "3.1" not in x, 
        "deepseek" not in x,
        "mixtral" not in x,
        x
    ))

    # Failsafe local: se a API da Groq negar acesso ao /models (erro 403), injetamos um fallback conhecido
    if not valid_models:
        logger.warning("Groq /models retornou vazio. Injetando fallback seguro.")
        return ["llama-3.3-70b-versatile"]

    return valid_models


def get_nvidia_models() -> list[str]:
    """
    Busca heurística na Nvidia API para modelos LLM corporativos (128k+).
    Explora famílias Llama 3.3, DeepSeek, Nemotron e Qwen.
    """
    if not config.NVIDIA_API_KEY:
        return []

    url = "https://integrate.api.nvidia.com/v1/models"
    headers = {"Authorization": f"Bearer {config.NVIDIA_API_KEY}"}
    data = _fetch_json(url, headers)

    valid_models = []
    for model in data.get("data", []):
        name = model.get("id", "").lower()
        # Nvidia costuma oferecer modelos de 128k nas famílias Llama 3.x e DeepSeek
        if any(tech in name for tech in ["llama-3.3-70b", "llama-3.1-70b", "deepseek-v3", "deepseek-r1", "nemotron-70b", "qwen2.5-72b"]):
            valid_models.append(name)

    # Ordem de preferência: Llama 3.3 > Llama 3.1 > Nemotron > DeepSeek
    valid_models.sort(key=lambda x: (
        "llama-3.3" not in x, 
        "llama-3.1" not in x, 
        "nemotron" not in x,
        "deepseek" not in x,
        x
    ))
    return valid_models


def get_gemini_models() -> list[str]:
    """
    Busca modelos na Gemini API.
    Aprovado: usar modelos >= 2.0 (visando 2.5+). Contexto do Gemini costuma ser >= 1M.
    """
    if not config.GEMINI_API_KEY:
        return []

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={config.GEMINI_API_KEY}"
    data = _fetch_json(url)

    valid_models = []
    for model in data.get("models", []):
        # Gemini model names look like: models/gemini-2.0-flash-lite-preview-0205
        name = model.get("name", "").replace("models/", "").lower()
        
        # Filtra por gemini-[versão maior >= 2]
        import re
        match = re.search(r"gemini-(\d+)\.", name)
        if match:
            major_version = int(match.group(1))
            if major_version >= 2:
                # Buscamos apenas Pro e Flash (ignorando modelos vision puros/experimentais isolados)
                if any(tier in name for tier in ["pro", "flash"]):
                    valid_models.append(name)

    # Se a API não retornar nada >= 2.0 (improvável), não caímos no 1.5. 
    # Mantemos a fila limpa ou deixamos para o failsafe final no get_fallback_queue


    # Ordena para preferir Pro sobre Flash se possível, e versões mais novas primeiro
    valid_models.sort(key=lambda x: ("pro" not in x, x), reverse=True)
    return valid_models


def get_fallback_queue() -> list[dict]:
    """
    Monta a Fila Mágica de Fallback.
    Consulta cada API, coleta os N melhores modelos que bateram nas heurísticas,
    e devolve a lista encadeada (Groq -> Nvidia -> Gemini).
    """
    global _FALLBACK_QUEUE_CACHE
    if _FALLBACK_QUEUE_CACHE:
        return _FALLBACK_QUEUE_CACHE

    logger.info("🔍 Descobrindo LLMs disponíveis nas APIs (Contexto >= 125k)...")
    queue = []

    # 1. Groq (Prioridade 1, ultra-rápido)
    groq_models = get_groq_models()
    for m in groq_models[:2]:  # Pega até os 2 melhores da Groq
        queue.append({"provider": "groq", "model": m})

    # 2. Nvidia (Prioridade 2, forte fallback corporativo)
    nvidia_models = get_nvidia_models()
    for m in nvidia_models[:2]:
        queue.append({"provider": "nvidia", "model": m})

    # 3. Gemini (Prioridade 3, contexto estratosférico)
    gemini_models = get_gemini_models()
    for m in gemini_models[:2]:
        queue.append({"provider": "gemini", "model": m})

    # Failsafe extremo caso não consiga ler nenhuma API (dns morto, timeout)
    if not queue:
        logger.warning("⚠️ Descoberta dinâmica falhou ou não encontrou modelos ideais. Usando Failsafe Moderno.")
        queue = [
            {"provider": "groq", "model": "llama-3.3-70b-versatile"},
            {"provider": "nvidia", "model": "meta/llama-3.3-70b-instruct"},
            {"provider": "gemini", "model": "gemini-2.0-pro-exp-0205"} # Fallback 2.5+ target
        ]

    _FALLBACK_QUEUE_CACHE = queue
    
    # Exibe a fila montada
    log_queue = " -> ".join([f"{q['provider']}({q['model']})" for q in queue])
    logger.info("✨ Fila de Fallback Dinâmica: %s", log_queue)

    return queue
