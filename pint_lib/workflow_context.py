import sys

from .utils import isYes
from .claude_engine import ClaudeEngine
from .open_ai_engine import OpenAIEngine
from .external_engine import ExternalEngine


DEFAULT_MAX_PROMPT_LENGTH = 100000
DEFAULT_MAX_TOKENS = 4096


class WorkflowContext:
    def __init__(self, model_data=None):
        if not model_data:
            return

        # Config from model_data
        self.start_from = int(model_data.get("start_from", 0))
        self.precheck_system = model_data.get(
            "precheck_system",
            "You are helping to automate a workflow.  You will be asked a question to verify the information you have given. You must only answer the question in EXACTLY the format requested. The answer will only ever be read by a computer, NEVER add any other commentary or automated processing will fail. It is more important to give a correctly formatted answer than to be sure the answer is correct.",
        )

        self.max_docs = model_data.get("max_documents")
        self.max_tokens = int(model_data.get("max_tokens", DEFAULT_MAX_TOKENS))
        self.max_prompt_length = int(
            model_data.get("max_prompt_length", DEFAULT_MAX_PROMPT_LENGTH)
        )
        self.max_doc_length = int(model_data.get("max_document_length", sys.maxsize))

        # Responses are stored so that they are not repeated later
        # If you want to clear the cache, delete the cache folder, or you can change the key in the specific api file
        self.data_folder = model_data.get(
            "files_folder", model_data.resolve_path("files")
        )
        self.cache_folder = model_data.get(
            "cache_folder", model_data.resolve_path("cache/api")
        )
        self.data_cache_folder = model_data.get(
            "self_data.data_cache_folder", model_data.resolve_path("cache/data")
        )

        self.which_api = model_data.get("model")
        self.api_key = model_data.get("api_key")
        self.api_url = model_data.get("api_url")

        self.column_name = model_data.get("column_name", "pubmed_id")
        # There is an alternative to use a local script to get pubmed data
        self.use_pubmed_api = isYes(model_data.get("use_pubmed_api", "true"))
        self.use_pubmed_search = isYes(model_data.get("use_pubmed_search", "false"))

        # Runtime state
        self.data_store = {}
        self.output_data = {}
        self.final_output = {}
        self.debug = {}
        self.ordered_column_list = []
        self.reply_count = 0
        self.script_returncode = 0
        self.llm_engine = None

    def reinit(self, model_data) -> None:
        self.__init__(model_data)

    def setup_llm_engine(self, model_data) -> None:
        engine_kwargs = {
            "model_data": model_data,
            "cache_folder": self.cache_folder,
            "max_tokens": self.max_tokens,
        }
        if self.api_key:
            engine_kwargs["key"] = self.api_key
        if self.api_url:
            engine_kwargs["api_url"] = self.api_url

        api_name = self.which_api.lower()
        if api_name.startswith(("claude", "anthropic")):
            self.llm_engine = ClaudeEngine(**engine_kwargs)
        elif api_name.startswith(("gpt", "chatgpt", "openai")):
            self.llm_engine = OpenAIEngine(**engine_kwargs)
        elif api_name.startswith(("external", "local", "ollama")):
            self.llm_engine = ExternalEngine(**engine_kwargs)
