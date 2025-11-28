import json
import subprocess

from .prompt_cache_sqlite import PromptCache  # Import the SQLite-based cache


class ExternalEngine:
    def __init__(self, model_data, cache_folder="cache", max_tokens=4096):
        """Initialize the engine with caching using SQLite."""

        self.cache = PromptCache(cache_folder)  # Use the imported cache class
        self.max_tokens = max_tokens  # note not used for external engine
        self.model_engine = model_data.get("model_name")
        self.llm_script = model_data.resolve_path(model_data.get("llm_script"))
        if self.llm_script is None:
            raise RuntimeError(
                "To use an External LLM script, llm_script must be specified in the config file."
            )

    def prompt(self, prompt, system=""):
        """Generates a response using the external script, with caching."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        response = self.create_chat_completion(messages)
        return response["choices"][0]["message"]["content"]

    def create_chat_completion(self, messages):
        """Handles chat completion with caching support."""
        # Extract system and user messages
        prompt = ""
        system = ""
        for m in messages:
            if m["role"] == "user":
                prompt += m["content"]
            if m["role"] == "system":
                system += m["content"]

        # Check cache first

        cached_response = self.cache.get_cached_response(
            self.model_engine, system, prompt
        )
        if cached_response:
            return {"choices": [cached_response]}

        # Prepare the prompt for the external script
        local_prompt = json.dumps({"prompt": prompt, "system": system})

        # Run the external script
        result = subprocess.run(
            [self.llm_script],
            input=local_prompt,
            capture_output=True,
            text=True,
            check=True,
        )

        # Process the output
        content = result.stdout.strip()
        message = {"message": {"content": content}}

        # Save the response to cache
        self.cache.save_response(self.model_engine, system, prompt, message)

        return {"choices": [message]}
