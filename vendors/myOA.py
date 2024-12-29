

from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from models import model_ids
from tools import FileManager
import json

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODEL_NAME = "grok-beta"
XAI_API_KEY = os.getenv("XAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")




# Agent class definition
class Agent:
    """Agent class for interacting with OpenAI's API."""
    def __init__(self, model='gpt-4o-mini',
                 system_prompt='You are a helpful assistant',
                 messages=[],
                 max_tokens=4096,
                 temperature=0.5,
                 files=None,
                 **kwargs):
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.messages = messages
        self.model = model
        self.response = None
        self.initialize_client()
        self.initialize_messages(system_prompt)
        self.upload_files(files)

    def initialize_messages(self,system_prompt):
        if self.messages==[]:
            self.messages.append({'role':'system','content':system_prompt})
    def upload_files(self,files):
        if files:
            for filepath in files:
                file=open(filepath, "rb")
                file_content = file.read()
                self.messages.append({'role':'developer','content':str(file_content)})
            print('Files uploaded')


    def initialize_client(self):
        vendor_name=model_ids[self.model]['vendor']
        if vendor_name=='grok':
            self.client = OpenAI(
            api_key=XAI_API_KEY,
            base_url="https://api.x.ai/v1",
        )
        elif vendor_name=='gemini':
            self.client = OpenAI(
            api_key=GOOGLE_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/")
        else:
            self.client = OpenAI(
            api_key=OPENAI_API_KEY)
        
        logging.info(f'client initialized with { vendor_name} style model')


    def print_messages(self):
        """Prints the conversation history in a user-friendly format."""
        print("=====================")
        print("      Messages:")
        print("=====================")
        for message in self.messages:
            role = message['role'].capitalize()
            content = message['content']
            print(f"\n{role}:")
            print(content)


    def chat(self, prompt, fm=False,files=[]):
        self.upload_files(files)
        """Initiate chat with the assistant"""
        self.messages.append({'role': 'user', 'content': prompt})

        if fm:
            if files!=[]:
                self.response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=self.messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format=FileManager,
                )
            else:
                self.response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=self.messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format=FileManager,
                )

            self.handle_file_response()
        else:
            if files!=[]:
                self.response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=self.messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            else:
                self.response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=self.messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            self.messages.append({'role': 'assistant', 'content': self.response.choices[0].message.content})

        logging.info("Chat completed.")
        self.print_messages()

    async def achat(self, prompt, fm=False):
        """Initiate chat with the assistant"""
        self.messages.append({'role': 'user', 'content': prompt})

        if fm:
            self.stream = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=FileManager,
                stream=True,
            )

            self.handle_file_response()
        else:
            self.stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
        self.response=''
        
        for chunk in self.stream:
            print(chunk.choices[0].delta.content or "", end="")
            self.response=self.response+str(chunk.choices[0].delta.content)

        self.messages.append({'role':'assistant','content':str(self.response)})
            

        logging.info("Chat completed.")
        self.print_messages()

    def handle_file_response(self):
        """Handle the file response and write the content to a file in the 'local' subdirectory"""
        file_content = json.loads(self.response.choices[0].message.content)['content']
        file_name = json.loads(self.response.choices[0].message.content)['name_no_ext']
        file_ext = json.loads(self.response.choices[0].message.content)['allowed_file_ext']

        # Create the 'local' subdirectory if it doesn't exist
        local_dir = "local"
        os.makedirs(local_dir, exist_ok=True)

        file_path = os.path.join(local_dir, f"{file_name}{file_ext}")
        logging.info(f"Writing file: {file_path}")

        try:
            with open(file_path, "w") as f:
                f.write(file_content)
            logging.info(f"File '{file_path}' written")
        except Exception as e:
            logging.error(f"Error writing file '{file_path}': {e}")