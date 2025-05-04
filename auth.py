import streamlit as st
import yaml
import os
from yaml.loader import SafeLoader

# Load configuration from file
def load_config():
    config_file = "config.yaml"
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            return yaml.load(file, Loader=SafeLoader)
    else:
        # Create default config with pre-hashed passwords
        config = {
            'credentials': {
                'usernames': {
                    'user': {
                        'email': 'user@example.com',
                        'name': 'Regular User',
                    },
                    'admin': {
                        'email': 'admin@example.com',
                        'name': 'Admin User',
                    }
                }
            }
        }
        with open(config_file, 'w') as file:
            yaml.dump(config, file)
        return config

# Simple custom login function
def custom_login():
    # Load authentication config
    config = load_config()
    
    if not st.session_state['authenticated']:
        with st.sidebar:
            st.title("🔐 Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                st.markdown("**Demo credentials:**")
                st.info("Username: **user** or **admin**\nPassword: **password123** (for user) or **admin123** (for admin)")
                submit = st.form_submit_button("Login")
                
                if submit:
                    # Demo mode - hardcoded credentials check
                    if username == "user" and password == "password123":
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = username
                        st.session_state['name'] = "Regular User"
                        st.rerun()
                    elif username == "admin" and password == "admin123":
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = username
                        st.session_state['name'] = "Admin User"
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        # Show minimal content when not logged in
        st.title("🏠 Real Estate Analytics Dashboard")
        st.info("Please log in using the sidebar to access the dashboard.")
        return False
    else:
        # Show logout button in sidebar
        with st.sidebar:
            st.title(f"👋 Welcome, {st.session_state['name']}")
            if st.button("Logout"):
                st.session_state['authenticated'] = False
                st.session_state['username'] = None
                st.session_state['name'] = None
                st.rerun()
        return True 