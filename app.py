import streamlit as st
import os
from pathlib import Path
import json
import asyncio
from models import model_ids
import streamlit as st
import tempfile
import os
from src.project_explorer import show_project_explorer
from chat import manage_chat

def initialize_session_state_variables():
    # Initialize session state
    if "selected_item" not in st.session_state:
        st.session_state.selected_item = None
    # Initialize session state
    if 'current_agent' not in st.session_state:
        st.session_state.current_agent = None
    if 'agents_config' not in st.session_state:
        st.session_state.agents_config = {}
    if 'streaming_enabled' not in st.session_state:
        st.session_state.streaming_enabled = False
        # Initialize files list in session state if not exists
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = set()


def load_agents_config():
    """Load saved agent configurations from a JSON file"""
    try:
        with open('agents_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_agents_config():
    """Save current agent configurations to a JSON file"""
    with open('agents_config.json', 'w') as f:
        json.dump(st.session_state.agents_config, f)


@st.dialog("Configure AI Agent")
def show_agent_settings_dialog():
    """Show agent settings in a dialog"""
    st.subheader("Agent Configuration")
    
    agent_name = st.text_input("Agent Name")
    model = st.selectbox("Model", list(model_ids.keys()))
    
    col1, col2 = st.columns(2)
    with col1:
        max_tokens = st.slider("Max Tokens", 256, 8192, 4096)
    with col2:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
    
    system_prompt = st.text_area("System Prompt", "You are a helpful assistant")
    
    if st.button("Save Agent"):
        if agent_name:
            st.session_state.agents_config[agent_name] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system_prompt": system_prompt
            }
            save_agents_config()
            st.success(f"Agent {agent_name} saved successfully!")
            st.rerun()
        else:
            st.error("Please provide an agent name")


def show_file_upload():
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)
    upload_temp_files(uploaded_files)

def upload_temp_files(uploaded_files):
    if uploaded_files:
            # Save uploaded files and get paths
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    st.session_state.uploaded_files.append(tmp_file.name)

def show_agents_settings():
    # Agent selection and settings
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.selected_agent = st.selectbox(
            "Select Agent",
            list(st.session_state.agents_config.keys()),
            key="agent_selector"
        )
    with col2:
        if st.button("⚙️", key="settings"):
            show_agent_settings_dialog()


def initialize_agents_config():
    # Load saved agent configurations
    if not st.session_state.agents_config:
        st.session_state.agents_config = load_agents_config()

def main():
    st.title("Project Workspace")

    initialize_session_state_variables()

    initialize_agents_config()
    
    # Sidebar
    with st.sidebar:
        st.header("Chat")
        
        show_agents_settings()
        
        show_file_upload()

        st.subheader('Messages')
        
        asyncio.run(manage_chat())

    show_project_explorer()

if __name__ == "__main__":
    main()