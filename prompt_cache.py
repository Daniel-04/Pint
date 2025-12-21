import os
import json
import hashlib
from typing import Optional, Dict, Any


class PromptCache:
    def __init__(
        self, cache_folder: str = "cache", cache_key: str = "prompt-caching-v1"
    ):
        self.cache_folder = cache_folder
        self.cache_key = cache_key
        os.makedirs(self.cache_folder, exist_ok=True)  # Ensure cache directory exists

    def _generate_hash(self, model_engine, system: str, prompt: str) -> str:
        hashkey = ".".join([self.cache_key, model_engine, system, prompt])
        return hashlib.md5(hashkey.encode()).hexdigest()

    def get_cached_response(
        self,
        model_engine,
        system: str,
        prompt: str,
    ) -> Optional[Dict[str, Any]]:
        hash_value = self._generate_hash(model_engine, system, prompt)
        filename = f"{self.cache_folder}/{hash_value}.json"

        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                return json.load(file)  # Return cached response

        return None  # No cached response

    def save_response(
        self, model_engine, system: str, prompt: str, response: Dict[str, Any]
    ) -> None:
        hash_value = self._generate_hash(model_engine, system, prompt)
        filename = f"{self.cache_folder}/{hash_value}.json"

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(response, file)
