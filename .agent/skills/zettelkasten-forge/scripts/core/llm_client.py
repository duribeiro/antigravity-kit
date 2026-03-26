"""
Agnostic LLM Client for Zettelkasten Forge.
Implements a Dynamic Fallback Strategy reading from the Magical Queue.
Returns strictly parsed JSON dictionaries.
"""
import json
import logging
import time
from typing import Any

from .config import (
    GROQ_API_KEY, NVIDIA_API_KEY, GEMINI_API_KEY, LLM_TEMPERATURE
)
from .model_discovery import get_fallback_queue

logger = logging.getLogger("llm_client")

def _parse_and_validate_json(raw_text: str) -> dict[str, Any]:
    """Tries to decode JSON from the LLM output."""
    try:
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
        return json.loads(raw_text.strip())
    except json.JSONDecodeError as err:
        logger.error("Error decoding JSON from LLM: %s", err)
        logger.error("Raw response: %s", raw_text[:300])
        return {}

def ask_llm(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """
    Sends a prompt to the LLM APIs using a dynamic fallback sequence.
    Expects a JSON schema from the LLM.
    """
    raw_json = None
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    fallback_queue = get_fallback_queue()

    for attempt in fallback_queue:
        provider = attempt["provider"]
        model_name = attempt["model"]

        if provider == "groq" and GROQ_API_KEY:
            try:
                from groq import Groq
                logger.info("  └─ Calling LLM (Groq: %s)...", model_name)
                client = Groq(api_key=GROQ_API_KEY)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=LLM_TEMPERATURE,
                    response_format={"type": "json_object"}
                )
                raw_json = response.choices[0].message.content
                if raw_json:
                    break
            except Exception as e:
                logger.warning("Groq failure (%s): %s", model_name, str(e))
                time.sleep(1)

        elif provider == "nvidia" and NVIDIA_API_KEY:
            try:
                from openai import OpenAI
                logger.info("  └─ Calling LLM (Nvidia: %s)...", model_name)
                client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=LLM_TEMPERATURE,
                    response_format={"type": "json_object"}
                )
                raw_json = response.choices[0].message.content
                if raw_json:
                    break
            except Exception as e:
                logger.warning("Nvidia failure (%s): %s", model_name, str(e))
                time.sleep(1)

        elif provider == "gemini" and GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                logger.info("  └─ Calling LLM (Gemini: %s)...", model_name)
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=LLM_TEMPERATURE, 
                        response_mime_type="application/json"
                    )
                )
                response = model.generate_content(user_prompt)
                raw_json = response.text.strip()
                if raw_json:
                    break
            except Exception as e:
                logger.error("Gemini failure (%s): %s", model_name, str(e))
                time.sleep(1)

    if not raw_json:
        logger.error("❌ Todos os LLMs da Fila de Fallback falharam. Retornando dict vazio.")
        return {}

    return _parse_and_validate_json(raw_json)
