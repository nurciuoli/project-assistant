from vendors.myOA import Agent as GptAgent
from vendors.myClaude import Agent as ClaudeAgent
from vendors.myLlama import Agent as LlamaAgent
from vendors.myPerplexity import Agent as PerplexityAgent
from models import model_ids
import streamlit as st

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
        
        if prompt := st.chat_input("Message your AI assistant..."):

            # Display chat messages from agent's history
            if hasattr(st.session_state.current_agent, 'messages'):
                for message in st.session_state.current_agent.messages:
                    if message['role']!="developer":
                        with st.chat_message(message['role']):
                            st.write(message['content'])

            with st.chat_message("user"):
                st.write(prompt)

            # Get AI response            
            try:
                if streaming_enabled:
                    with st.chat_message("assistant"):
                        stream = st.session_state.current_agent.achat(prompt=prompt, files=st.session_state.uploaded_files)
                        response =st.write_stream(stream)
                        # Append the complete response to the agent's message history
                        st.session_state.current_agent.messages.append({'role': 'assistant', 'content': response})
                        
                else:
                    st.session_state.current_agent.chat(prompt=prompt, files=st.session_state.uploaded_files)
                    st.rerun()  # Refresh to show new messages
            except Exception as e:
                st.error(f"Error getting response: {str(e)}")
        
        