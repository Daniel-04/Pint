import os

from .prompt_cache_sqlite import PromptCache


class ClaudeEngine:

    def __init__(self, model_data, key=None, cache_folder="cache", max_tokens=4096):
        try:
            import anthropic
        except ModuleNotFoundError as e:
            raise RuntimeError(
                "To use Claude, the anthropic package must be installed."
            ) from e

        if key is None:
            key = os.environ["ANTHROPIC_API_KEY"]
        if key is None:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        self.max_tokens = max_tokens
        self.model_engine = model_data.get("model_name")
        self.client = anthropic.Anthropic(
            api_key=key,
        )
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
    def create_chat_completion(self, messages):
        prompt = ""
        system = ""
        for m in messages:
            if m["role"] == "user":
                prompt += m["content"]
            if m["role"] == "system":
                system += m["content"]

        cached_response = self.cache.get_cached_response(
            self.model_engine, system, prompt
        )
        if cached_response:
            return {"choices": [cached_response]}

        message = self.client.messages.create(
            model=self.model_engine,
            system=system,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        response = {"message": {"content": message.content[0].text}}

        # Save response to cache
        self.cache.save_response(self.model_engine, system, prompt, response)

        return {"choices": [response]}
