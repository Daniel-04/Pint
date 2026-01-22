import json
import subprocess
from typing import List, Dict, Any

from .prompt_cache_sqlite import PromptCache  # Import the SQLite-based cache
from .retry import retry


class ExternalEngine:
    def __init__(self, model_data, cache_folder: str = "cache", max_tokens: int = 4096):
        """Initialize the engine with caching using SQLite."""

        self.cache = PromptCache(cache_folder)  # Use the imported cache class
        self.max_tokens = max_tokens  # note not used for external engine
        self.model_engine = model_data.get("model_name")
        self.llm_script = model_data.resolve_path(model_data.get("llm_script"))
        if self.llm_script is None:
            raise RuntimeError(
                "To use an External LLM script, llm_script must be specified in the config file."
            )

    def prompt(self, prompt: str, system: str = ""):
        """Generates a response using the external script, with caching."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        response = self.create_chat_completion(messages)
        return response["choices"][0]["message"]["content"]

    @retry
    def create_chat_completion(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Handles chat completion with caching support."""
        # Extract system and user messages
        system = " ".join(m["content"] for m in messages if m["role"] == "system")
        prompt = " ".join(m["content"] for m in messages if m["role"] == "user")

        # Check cache first
        cached_response = self.cache.get_cached_response(
            self.model_engine, system, prompt
        )
        if cached_response:
            return {"choices": [cached_response]}

        # Prepare the prompt for the external script
        payload = {
            "messages": messages,
            "system": system,
            "prompt": prompt,
        }

        local_prompt = json.dumps(payload)

        # Run the external script
        try:
            result = subprocess.run(
                [self.llm_script],
                input=local_prompt,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"External LLM script failed: {e.stderr or e.stdout}"
            ) from e

        # Process the output
        content = result.stdout.strip()
        wrapped = {
            "message": {
                "role": "assistant",
                "content": content,
            }
        }

        # Save the response to cache
        self.cache.save_response(self.model_engine, system, prompt, wrapped)
        return {"choices": [wrapped]}
