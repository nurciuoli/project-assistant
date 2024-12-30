from vendors.myOA import Agent as GptAgent
from vendors.myClaude import Agent as ClaudeAgent
from vendors.myLlama import Agent as LlamaAgent
from vendors.myPerplexity import Agent as PerplexityAgent
from models import model_ids
import streamlit as st
import openai
import os
import json
from tools import FileManager
def initialize_agent(model='gpt-4o-mini', max_tokens=4096, temperature=0.5, 
                    system_prompt='You are a helpful assistant', messages=[]):
    """Initialize an AI agent based on the selected model"""
    agent_classes = {
        'llama': LlamaAgent,
        'claude': ClaudeAgent,
        'gpt': GptAgent,
        'perplex': PerplexityAgent,
        'gemini': GptAgent,
        'grok': GptAgent,
    }
    
    AgentClass = agent_classes[model_ids[model]['vendor']]
    return AgentClass(model=model, max_tokens=max_tokens, messages=messages,
                     temperature=temperature, system_prompt=system_prompt)



def handle_stream(response_stream):
    function_arguments = ""
    function_name = ""
    is_collecting_function_args = False

    for part in response_stream:
        delta = part.choices[0].delta
        finish_reason = part.choices[0].finish_reason
        if delta.content:
            yield delta.content



        if delta.tool_calls:
            is_collecting_function_args = True
            tool_call = delta.tool_calls[0]

            if tool_call.function.name:
                function_name = tool_call.function.name
                #print(f"Function name: '{function_name}'")
            
            # Process function arguments delta
            if tool_call.function.arguments:
                function_arguments += tool_call.function.arguments
                #print(f"Arguments: {function_arguments}")

        # Process tool call with complete arguments
        if finish_reason == "tool_calls" and is_collecting_function_args:
            print(f"Function call '{function_name}' is complete.")
            args = json.loads(function_arguments)
            #print("Complete function arguments:")
            #print(json.dumps(args, indent=2))

            file_content = args['content']
            file_name = args['name_no_ext']
            file_ext = args['allowed_file_ext']

            # Create the 'local' subdirectory if it doesn't exist
            local_dir = "local"
            os.makedirs(local_dir, exist_ok=True)

            file_path = os.path.join(local_dir, f"{file_name}{file_ext}")

            try:
                with open(file_path, "w") as f:
                    f.write(file_content)
            except Exception as e:
                pass
        
            # Reset for the next potential function call
            function_arguments = ""
            function_name = ""
            is_collecting_function_args = False

tool_mapping = {
    "FileManager": FileManager,  # Assuming FileManager is the class you want to use
    # Add more tools as needed
}



async def manage_chat():
    # Chat interface
    if st.session_state.selected_agent and st.session_state.selected_agent in st.session_state.agents_config:
        config = st.session_state.agents_config[st.session_state.selected_agent]
        
        if st.session_state.current_agent is None:
            st.session_state.current_agent = initialize_agent(
                model=config["model"],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                system_prompt=config["system_prompt"]
            )
        
        # Add a toggle for streaming
        streaming_enabled = st.checkbox("Enable Streaming", value=False)
        
                # Add multi-select for tools
        selected_tools = st.sidebar.multiselect(
            "Select Tools",
            options=list(tool_mapping.keys()),  # Use the keys from the mapping
            default=[]
        )

        if selected_tools:

            tools = [openai.pydantic_function_tool(tool_mapping[tool]) for tool in selected_tools]
        else:
            tools=None
        
        if prompt := st.chat_input("Message your AI assistant..."):

            # Display chat messages from agent's history
            if hasattr(st.session_state.current_agent, 'messages'):
                for message in st.session_state.current_agent.messages:
                    if message['role'] != "developer":
                        with st.chat_message(message['role']):
                            st.write(message['content'])

            with st.chat_message("user"):
                st.write(prompt)

            # Get AI response            
            try:
                if streaming_enabled:
                    with st.chat_message("assistant"):
                        stream = st.session_state.current_agent.achat(
                            prompt=prompt,
                            files=st.session_state.uploaded_files,
                            tools=tools  # Pass selected tools
                        )
                        response = st.write_stream(handle_stream(stream))
                        # Append the complete response to the agent's message history
                        st.session_state.current_agent.messages.append({'role': 'assistant', 'content': response})
                        
                else:
                    st.session_state.current_agent.chat(
                        prompt=prompt,
                        files=st.session_state.uploaded_files,
                        tools=tools  # Pass selected tools
                    )
                    st.rerun()  # Refresh to show new messages
            except Exception as e:
                st.error(f"Error getting response: {str(e)}")
        
        