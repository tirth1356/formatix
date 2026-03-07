"""
Groq client for cloud LLM inference.
Endpoint: https://api.groq.com/openai/v1/chat/completions
"""
import json
from typing import Optional
from groq import AsyncGroq


class GroqClient:
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.client = AsyncGroq(api_key=api_key) if api_key else None
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Send chat completion request to Groq. Returns assistant message content."""
        if not self.client:
            raise ValueError("GROQ_API_KEY not set")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if "json" in prompt.lower() or (system and "json" in system.lower()):
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
    ) -> dict:
        """Generate and parse JSON from model response."""
        raw = await self.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
        )
        text = raw.strip()
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end] if end > start else text[start:]
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end] if end > start else text[start:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": raw}
