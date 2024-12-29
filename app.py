import streamlit as st
import os
from pathlib import Path
import json
import asyncio
from vendors.myOA import Agent as GptAgent
from vendors.myClaude import Agent as ClaudeAgent
from vendors.myLlama import Agent as LlamaAgent
from vendors.myPerplexity import Agent as PerplexityAgent
from models import model_ids
import streamlit as st
import tempfile
import os

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

def get_top_level_contents(path):
    """Get only the top-level files and folders in the given path"""
    contents = []
    try:
        for entry in os.scandir(path):
            contents.append({
                "label": entry.name,
                "type": "folder" if entry.is_dir() else "file"
            })
        return sorted(contents, key=lambda x: (x["type"] != "folder", x["label"].lower()))
    except PermissionError:
        st.error(f"Permission denied accessing {path}")
        return []

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

async def get_streaming_response(agent, prompt):
    """Handle streaming response from agent"""
    await agent.achat(prompt)


@st.dialog("File/Folder Details")
def show_file_folder_dialog():
    """Display file or folder details in a dialog."""
    if st.session_state.selected_item:
        item = st.session_state.selected_item
        if item["type"] == "file":
            st.subheader(f"File: {item['name']}")
            try:
                with open(item["path"], "r") as f:
                    content = f.read()
                st.text_area("Content", content, height=300)
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        elif item["type"] == "folder":
            st.subheader(f"Folder: {item['name']}")
            try:
                for entry in os.scandir(item["path"]):
                    icon = "📁" if entry.is_dir() else "📄"
                    st.write(f"{icon} {entry.name}")
            except Exception as e:
                st.error(f"Error reading folder: {str(e)}")

def get_top_level_contents(path):
    """Get the top-level files and folders in a given path."""
    try:
        return [
            {"name": entry.name, "path": entry.path, "type": "folder" if entry.is_dir() else "file"}
            for entry in os.scandir(path)
        ]
    except PermissionError:
        st.error("Permission denied")
        return []

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

def manage_chat():
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
        
        # Chat input
        if prompt := st.chat_input("Message your AI assistant..."):
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                try:

                    st.session_state.current_agent.chat(prompt=prompt,files=st.session_state.uploaded_files)
                        
                    st.rerun()  # Refresh to show new messages
                        
                except Exception as e:
                    st.error(f"Error getting response: {str(e)}")

def show_project_explorer():
    st.subheader("Project Explorer")
    
    # Display current directory
    current_path = os.getcwd()
    st.write(f"Current directory: `{current_path}`")

    # Define the subdirectory name
    subdirectory_name = "local"
    subdirectory_path = os.path.join(current_path, subdirectory_name)

    # Create the subdirectory if it doesn't already exist
    if not os.path.exists(subdirectory_path):
        os.makedirs(subdirectory_path)
        st.write(f"Created directory: `{subdirectory_path}`")

    # Display top-level files and folders
    contents = get_top_level_contents(subdirectory_path)
    
    
    # Display files with selection toggles
    for item in contents:
        col1, col2, col3 = st.columns([1, 15, 4])
        
        with col1:
            st.write("📁" if item["type"] == "folder" else "📄")
        
        with col2:
            if st.button(item["name"], key=f"view_{item['path']}"):
                st.session_state.selected_item = item
                show_file_folder_dialog()
                
        with col3:
            if item["type"] == "file":  # Only show toggle for files
                if st.toggle("Select", key=f"toggle_{item['path']}", 
                           value=item["path"] in st.session_state.uploaded_files):
                    st.session_state.uploaded_files.add(item["path"])
                else:
                    st.session_state.uploaded_files.discard(item["path"])

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
        
        manage_chat()

    show_project_explorer()

if __name__ == "__main__":
    main()