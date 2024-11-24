from main import main
import streamlit as st

st.title("Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role" : "assistant", 
            "content" : "How can I help you?"
        }
    ]
    st.session_state["main"] = main()

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    main_app : main = st.session_state.main
    messages : list[dict] = st.session_state.messages
    messages.append({"role" : "user", "content" : prompt})
    st.chat_message("user").write(prompt)
    msg = main_app.chat(prompt)
    messages.append({"role" : "assistant", "content" : msg})
    st.chat_message("assistant").write(msg)
