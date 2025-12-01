import os

from .prompt_cache_sqlite import PromptCache
from .retry import retry


class ClaudeEngine:

    def __init__(self, model_data, key=None, cache_folder="cache", max_tokens=4096):
        try:
            import anthropic
        except ModuleNotFoundError as e:
            raise RuntimeError(
                "To use Claude, the anthropic package must be installed."
            ) from e

        if key is None:
            key = os.environ.get("ANTHROPIC_API_KEY")
        if key is None:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        self.model_engine = model_data.get("model_name")
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=key)
        self.cache_folder = cache_folder
        self.cache = PromptCache(cache_folder)  # Use the imported cache class

    def prompt(self, prompt, system=""):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        response = self.create_chat_completion(messages)
        return response["choices"][0]["message"]["content"]

    # This is used for API compatibility
    @retry
    def create_chat_completion(self, messages):
        system_msg = "".join(m["content"] for m in messages if m["role"] == "system")

        chat_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] != "system"
        ]

        system = system_msg
        prompt = "".join(m["content"] for m in chat_messages if m["role"] == "user")

        cached = self.cache.get_cached_response(self.model_engine, system, prompt)
        if cached:
            return {"choices": [cached]}

        response = self.client.messages.create(
            model=self.model_engine,
            system=system_msg,
            messages=chat_messages,
            max_tokens=self.max_tokens,
        )

        text = response.content[0].text
        wrapped = {
            "message": {
                "role": "assistant",
                "content": text,
            }
        }

        # Save response to cache
        self.cache.save_response(self.model_engine, system, prompt, wrapped)
        return {"choices": [wrapped]}
