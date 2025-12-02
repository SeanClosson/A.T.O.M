import lmstudio as lms
import yaml
from pathlib import Path

class LMSTUDIO():
    def __init__(self, config_file="config.yaml"):

        self.config_file = config_file

        # -----------------------------
        # Load YAML config safely
        # -----------------------------
        try:
            if not Path(self.config_file).exists():
                raise FileNotFoundError(f"Config file '{self.config_file}' not found.")

            with open(self.config_file, "r") as file:
                config = yaml.safe_load(file) or {}
        except Exception as e:
            print(f"[ERROR] Failed to load configuration: {e}")
            config = {}

        base_url = config['LLM']['BASE_URL']
        server_url = base_url.removeprefix("http://").removesuffix("/v1")

        self.SERVER_API_HOST = server_url
        lms.configure_default_client(self.SERVER_API_HOST)
        self.model = lms.llm(config['LLM']['MODEL_NAME'])
        self.loaded_llm_only = lms.list_loaded_models("llm")
        if self.loaded_llm_only[0].identifier == config['LLM']['MODEL_NAME']:
            print("Loaded LLM")

    def unload_model(self):
        print('Model unloaded')
        self.model.unload()

    def ls_model(self):
        print(self.loaded_llm_only)
