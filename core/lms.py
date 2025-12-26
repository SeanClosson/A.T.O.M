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
                self.config = yaml.safe_load(file) or {}
        except Exception as e:
            print(f"[ERROR] Failed to load configuration: {e}")
            self.config = {}

        base_url = self.config['LLM']['BASE_URL']
        server_url = base_url.removeprefix("http://").removesuffix("/v1")

        self.SERVER_API_HOST = server_url
        
        self.client = lms.get_default_client(api_host=self.SERVER_API_HOST)
        
        self.loaded_llm_only = lms.list_loaded_models("llm")
        # print(self.loaded_llm_only)
        # if self.loaded_llm_only[0].identifier == config['LLM']['MODEL_NAME']:
            # print("Loaded LLM")

    def unload_model(self):
        print('Unloading models ...')
        
        self.model.unload()
        self.summary_model.unload()

        print('\nModel unloaded')

    def ls_model(self):
        print(self.loaded_llm_only)

    def load_model(self):
        self.model = self.client.llm.load_new_instance(self.config['LLM']['MODEL_NAME'], 
                             config={
                                 'contextLength': 12000,
                                 'gpu':{
                                    'ratio': 0.84
                                 },
                             })
        
    def load_summary_model(self):
        self.summary_model = self.client.llm.load_new_instance(self.config['LLM']['SUMMARY_MODEL_NAME'], 
                             config={
                                 'contextLength': 8192,
                                 'gpu':{
                                    'ratio': 0.0
                                 },
                             })
        
        # print('Summary Model loaded')