import ollama as o
import base64
import logging
from ollama import Client
client = Client()
# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to chat with the Llama model
def chat(user_msg):
    """
    Sends a user message to the Llama model and returns the model's response.

    Parameters:
    - user_msg (str): The message from the user.

    Returns:
    - dict: The response from the Llama model.
    """
    messages = [{'role': 'user', 'content': user_msg}]
    response = client.chat('llama3', messages=messages, stream=False)
    logging.info("Chat message sent and response received.")
    return response

# Function to generate text based on a prompt
def generate(prompt, format=None):
    """
    Generates a response from the Llama model based on a given prompt.

    Parameters:
    - prompt (str): The prompt to generate text from.
    - format (str, optional): The format of the response. Defaults to None.

    Returns:
    - str: The generated response.
    """
    response = o.generate('llama3', prompt, stream=False, format=format)
    logging.info("Generated text from prompt.")
    return response['response']

# Function to generate text with images
def generate_w_images(prompt, images, stream=True):
    """
    Generates responses from the Llama model based on a prompt and images.

    Parameters:
    - prompt (str): The prompt to generate text from.
    - images (list): A list of images to include in the generation.
    - stream (bool, optional): Whether to stream the response. Defaults to True.
    """
    for response in o.generate('llava', prompt, images=images, stream=stream):
        print(response['response'], end='', flush=True)
    logging.info("Generated text with images from prompt.")
    print()

# Agent class for interacting with the Llama model
class Agent:
    def __init__(self, model='llama3.1', system_prompt='You are a helpful chat based assistant',messages=[], max_tokens=8000, temperature=0.5,tools=None,files=None):
        """
        Initializes the Agent with a model, system prompt, maximum token count, and temperature.

        Parameters:
        - model (str): The model identifier.
        - system_prompt (str): The system prompt to initialize conversations.
        - max_tokens (int): The maximum number of tokens to generate.
        - temperature (float): The temperature for generation.
        """
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model = model
        self.response = None
        self.tools=[]
        self.tool_inputs=None
        self.tool_outputs=None

        for tool in tools:
            self.tools.append({
        'type': 'function',
        'function': tool})

        self.messages = messages.copy()  # Make a copy of the messages to avoid modifying the original list

        # Only add the system prompt if the messages list is empty
        if not self.messages:
            self.messages.append({'role': 'assistant', 'content': system_prompt})
        logging.info(f"Agent initialized with model {model}.")

    def chat(self, user_msg, json_mode=False):
        """
        Continues the conversation with the user, sending their message to the model and returning the response.

        Parameters:
        - user_msg (str): The user's message.
        - json_mode (bool, optional): Whether to return the response in JSON format. Defaults to False.

        Returns:
        - str: The content of the model's response.
        """
        if json_mode:
            out_format = 'json'
        else:
            out_format = ''
        options = {'num_predict': self.max_tokens, 'temperature': self.temperature}

        self.messages.append({'role': 'user', 'content': user_msg})
        self.response = client.chat(self.model, messages=self.messages, stream=False, options=options, tools=self.tools)
        self.messages.append({'role': 'assistant', 'content': self.response['message']['content']})

        if 'tool_calls' in self.response['message']:
            print('hi')
            self.tool_inputs = self.response['message']['tool_calls']

        logging.info("Chat continued with user message.")
        return self.response['message']['content']
