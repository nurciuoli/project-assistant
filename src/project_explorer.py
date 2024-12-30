import streamlit as st
import os

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
