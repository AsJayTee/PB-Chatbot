from main import main
import streamlit as st

st.title("Psychology Blossom Assistant")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role" : "assistant", 
            "content" : "Thank you for contacting Psychology Blossom! How can I help you?"
        }
    ]
    st.session_state["main"] = main()

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

main_app : main = st.session_state.main
messages : list[dict] = st.session_state.messages

if prompt := st.chat_input():
    messages.append({"role" : "user", "content" : prompt})
    st.chat_message("user").write(prompt)
    with st.spinner("Finding out for you... 😊"):
        msg = main_app.chat(prompt)
    messages.append({"role" : "assistant", "content" : msg})
    st.chat_message("assistant").write(msg)

with st.sidebar:
        costs = main_app.get_new_costs()
        st.metric(
            "Embedding model costs", 
            f"${costs.get("embed_cost"):.6f}", 
            f"{costs.get("embed_diff"):.6f}",
            delta_color = "off"
        )
        st.metric(
            "GPT-4o model costs", 
            f"${costs.get("gpt_4o_cost"):.5f}", 
            f"{costs.get("gpt_4o_diff"):.5f}",
            delta_color = "off"
        )
        st.metric(
            "GPT-4o-mini model costs", 
            f"${costs.get("gpt_4o_mini_cost"):.6f}", 
            f"{costs.get("gpt_4o_mini_diff"):.6f}",
            delta_color = "off"
        )
