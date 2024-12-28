import requests
import os
from dotenv import load_dotenv
import logging
import time

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

logging.info("Perplexity configuration initialized.")

# Agent class definition
class Agent:
    """Agent class for interacting with Perplexity AI's API."""
    def __init__(self, system_prompt='Be precise and concise.', 
                 model='llama-3.1-sonar-small-128k-online',
                 messages=[], 
                 max_tokens=None,
                 temperature=0.2,
                 top_p=0.9,
                 return_citations=False,
                 **kwargs):
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.return_citations = return_citations
        self.history = messages
        self.model = model
        self.response = None
        self.url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        logging.info(f"Perplexity agent created with model {model}.")

        if messages==[]:
            messages.append({'role':'system','content':system_prompt})
            self.messages=messages
        else:
            self.messages=messages

    def chat(self, prompt):
        """Initiate chat with the assistant"""
        self.messages.append({'role':'user','content':prompt})
        
        payload = {
            "model": self.model,
            "messages": self.messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "return_citations": self.return_citations,
            "search_domain_filter": ["perplexity.ai"],
            "return_images": False,
            "return_related_questions": False,
            "search_recency_filter": "month",
            "top_k": 0,
            "stream": False,
            "presence_penalty": 0,
            "frequency_penalty": 1
        }

        self.response = requests.post(self.url, json=payload, headers=self.headers)
        response_data = self.response.json()
        
        # Extract the assistant's message from the response
        assistant_message = response_data['choices'][0]['message']['content']
        self.messages.append({'role':'assistant','content':assistant_message})

        print(assistant_message)
        
        logging.info("Chat completed.")