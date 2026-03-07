"""
Ollama client for local LLM inference.
Endpoint: http://localhost:11434/api/generate
"""
import json
import httpx
from typing import Optional


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.generate_url = f"{self.base_url}/api/generate"

    async def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        system: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Send generate request to Ollama. Returns full response text."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {"temperature": temperature},
        }
        if "json" in prompt.lower() or (system and "json" in system.lower()):
            payload["format"] = "json"
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.generate_url, json=payload)
            response.raise_for_status()
            data = response.json()

        if stream:
            # For stream=True we'd consume the stream; for now we use stream=False
            return ""

        return data.get("response", "")

    async def generate_json(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
    ) -> dict:
        """Generate and parse JSON from model response."""
        raw = await self.generate(
            model=model,
            prompt=prompt,
            stream=False,
            system=system,
            temperature=temperature,
        )
        # Extract JSON block if wrapped in markdown
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
