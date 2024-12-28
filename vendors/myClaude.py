import anthropic
import json
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Anthropic client
client = anthropic.Anthropic()
logging.info("Anthropic client initialized.")

# Function to send messages to the Anthropic API
def send_message(messages, system_prompt, model, max_tokens, temperature,tools=None):
    """
    Sends a message to the Anthropic API and returns the response content.

    Parameters:
    - messages: A list of message dictionaries.
    - system_prompt: The system prompt string.
    - model: The model identifier string.
    - max_tokens: The maximum number of tokens to generate.
    - temperature: The temperature for the generation.

    Returns:
    - The content of the response from the API.
    """
    try:
        if tools:

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
                tools=tools,
                tool_choice={"type": "auto"},
            )

            print(f"\nInitial Response:")
            print(f"Stop Reason: {response.stop_reason}")
            #print(f"Content: {response.content}")

            messages.append({"role":"assistant",
                             "content":response.content})

            while response.stop_reason == "tool_use":
                tool_use = next(block for block in response.content if block.type == "tool_use")
                tool_name = tool_use.name
                tool_input = tool_use.input

                print(f"\nTool Used: {tool_name}")
                #print(f"Tool Input:")
                #print(json.dumps(tool_input, indent=2))

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content":"written successfully",
                            }
                        ],
                    })
                response = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    tools=tools,
                    messages=messages
                )

                messages.append({"role":"assistant",
                                 "content":response.content})

                #print(f"\nResponse:")
                print(f"Stop Reason: {response.stop_reason}")
                #print(f"Content: {response.content}")

            return response

        else:
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            return message
    except Exception as e:
        logging.error(f"Error sending message to Anthropic API: {e}")
        return None

# Agent class for managing interactions
class Agent:
    def __init__(self, system_prompt='You are a helpful assistant',
                 name='assistant',
                 model="claude-3-sonnet-20240229",
                 messages=[],
                 max_tokens=1000,
                 temperature=0.5,
                 tools=None,files=None):
        """
        Initializes the Agent with default values or provided arguments.

        Parameters:
        - system_prompt: The default system prompt for the agent.
        - name: The name of the agent.
        - model: The model identifier for the agent.
        - max_tokens: The maximum number of tokens for the agent's responses.
        - temperature: The temperature for the agent's responses.
        """
        self.system_prompt = system_prompt
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.name = name
        self.response = None
        self.history = messages
        self.messages=None
        self.tools=tools
        self.files=files
        self.tool_input=None


    def __str__(self):
        # String representation of the Agent
        return f"Agent(Name: {self.name}, Model: {self.model})"

    def chat(self, user_prompt, attachments=None, json_mode=False):
        """
        Handles chatting with the user, processing attachments, and managing response modes.

        Parameters:
        - user_prompt: The user's input prompt.
        - attachments: Optional attachments to include in the prompt.
        - json_mode: Flag to determine if the response should be in JSON format.

        Returns:
        - The response from the agent.
        """
        logging.info(f"Chat initiated with prompt: {user_prompt}")
        full_prompt = ''
        if attachments is not None:
            for attachment in attachments:
                self.files.append(attachment)
        if self.files is not None:
            for file_path in self.files:
                try:
                    with open(file_path, 'r') as file:
                        content = file.read()
                        tag_label = os.path.basename(file_path)
                        full_prompt += f"<{tag_label}> {content} </{tag_label}>"
                except Exception as e:
                    logging.error(f"Error reading file {file_path}: {e}")

        full_prompt+=user_prompt

        self.history.append({"role": "user", "content": full_prompt})

        if json_mode==True:
            self.history.append({"role": "assistant", "content": "{"})

        response = send_message(self.history, self.system_prompt, self.model, self.max_tokens, self.temperature,self.tools)

        self.response = response
        self.print_response_and_append_messages()
        return response

    def print_response_and_append_messages(self):
        """
        Processes and prints the response messages, appending them to the messages list.

        Parameters:
        - response: The response to process.
        - json_mode: Flag to determine if the response should be processed as JSON.
        """
        msg_list=[]
        try:
            if self.tool_input is None:
                self.tool_input = []

            for item in self.history:
                if item['role'] == 'user':
                    if isinstance(item['content'], str):
                        msg_list.append({"role":"user",
                                        "content":item['content']})
                elif item['role'] == 'assistant':
                    if isinstance(item['content'], list):
                        for content in item['content']:
                            if content.type == 'tool_use':
                                self.tool_input.append({content.name: content.input})
                            elif content.type == 'text':
                                print(content.text)
                                msg_list.append({"role":'assistant',
                                                "content":content.text})
                    else:
                        msg_list.append({"role":'assistant',
                                        "content":item['content']})

            self.messages=msg_list

        except Exception as e:
            logging.error(f"Error processing response messages: {e}")
