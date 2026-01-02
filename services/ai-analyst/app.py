import streamlit as st
import google.generativeai as genai
from tools import SplunkConnector, IOCManager

# Page Config
st.set_page_config(page_title="AI SOC Analyst", page_icon="🛡️")

st.title("🛡️ AI SOC Analyst")
st.caption("Powered by Gemini 2.0 Flash Exp & Splunk")

# Initialize Splunk and IOC Tools
splunk = SplunkConnector()
ioc_manager = IOCManager()
tools_list = [splunk.search, ioc_manager.save_ioc]

import os

# Sidebar Configuration
with st.sidebar:
    st.header("Configuration")
    
    api_key_env = os.environ.get("GEMINI_API_KEY")
    if api_key_env:
        st.success("API Key loaded from environment")
        api_key = api_key_env
    else:
        api_key = st.text_input("Gemini API Key", type="password")

    st.divider()
    st.info("Ensure the Splunk container is running and accessible.")
    
    st.divider()
    st.header("Tracked IOCs")
    iocs = ioc_manager.get_iocs()
    if not iocs.empty:
        st.dataframe(iocs, hide_index=True)
    else:
        st.info("No IOCs found yet.")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None


# Setup Gemini
if api_key:
    genai.configure(api_key=api_key)
    
    if st.session_state.chat_session is None:
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            tools=tools_list
        )
        st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
else:
    st.warning("Please enter your Gemini API Key to start.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Handling
if prompt := st.chat_input("Analyze the security logs..."):
    if not api_key:
        st.error("API Key required!")
        st.stop()
    
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Response generation
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            response = st.session_state.chat_session.send_message(prompt)
            full_response = response.text
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
