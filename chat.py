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

async def get_streaming_response(agent, prompt,files):
    """Handle streaming response from agent"""
    stream = await agent.achat(prompt=prompt,files=files)
    response=""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            st.write(chunk.choices[0].delta.content)
            response+=chunk.choices[0].delta.content
    
    agent.messages.append({'role': 'assistant', 'content': response})

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
        
        # Display chat messages from agent's history
        if hasattr(st.session_state.current_agent, 'messages'):
            for message in st.session_state.current_agent.messages:
                if message['role']!="developer":
                    with st.chat_message(message['role']):
                        st.write(message['content'])
        
            # Add a toggle for streaming
        streaming_enabled = st.checkbox("Enable Streaming", value=False)
        
        if prompt := st.chat_input("Message your AI assistant..."):
            with st.chat_message("user"):
                st.write(prompt)

            # Get AI response            
            try:
                if streaming_enabled:
                    with st.chat_message("assistant"):
                        await get_streaming_response(st.session_state.current_agent, prompt,st.session_state.uploaded_files)
                else:
                    st.session_state.current_agent.chat(prompt=prompt, files=st.session_state.uploaded_files)
                    st.rerun()  # Refresh to show new messages
            except Exception as e:
                st.error(f"Error getting response: {str(e)}")