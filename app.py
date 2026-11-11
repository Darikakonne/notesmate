
import streamlit as st
from auth import create_supabase_client, register_user, login_user, logout_user
from chat_storage import load_user_chats, create_chat, save_chat, delete_chat
from document_reader import extract_text
from study_agent import create_study_assistant, ask_question

st.set_page_config(page_title="Notes Mate AI", page_icon="📚", layout="wide")

# Initialize session state
defaults = {
    "user": None,
    "vector_store": None,
    "file_name": None,
    "chats": {},
    "current_chat": None
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Connect to Supabase
try:
    if "supabase" not in st.session_state:
        st.session_state.supabase = create_supabase_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
except Exception as error:
    st.error(f"Supabase connection failed: {error}")
    st.stop()

supabase = st.session_state.supabase

# Load saved chats for the logged-in user
def initialize_chats(user):
    user_id = user.id
    chats = load_user_chats(supabase, user_id)

    if not chats:
        new_chat = create_chat(supabase, user_id)
        chats[new_chat["id"]] = {
            "title": new_chat["title"],
            "messages": new_chat["messages"] or []
        }

    st.session_state.chats = chats
    st.session_state.current_chat = next(iter(chats))

# Authentication
if st.session_state.user is None:
    st.title("📚 NotesMate")
    st.caption("Your personal AI-powered study companion")

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        st.subheader("Welcome Back!")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login", use_container_width=True)

        if login_button:
            try:
                response = login_user(supabase, email.strip(), password)
                if response.user is None:
                    st.error("Login failed. Please check your credentials.")
                else:
                    st.session_state.user = response.user
                    initialize_chats(response.user)
                    st.session_state.vector_store = None
                    st.session_state.file_name = None
                    st.success("Login successful!")
                    st.rerun()
            except Exception as error:
                st.error(f"Login failed: {error}")

    with signup_tab:
        st.subheader("Create Your Account")
        with st.form("signup_form"):
            new_email = st.text_input("Email address")
            new_password = st.text_input("Create password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            signup_button = st.form_submit_button("Create Account", use_container_width=True)

        if signup_button:
            if not new_email.strip() or not new_password:
                st.warning("Please enter your email and password.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must contain at least 6 characters.")
            else:
                try:
                    response = register_user(
                        supabase,
                        new_email.strip(),
                        new_password
                    )
                    if response.session is not None and response.user is not None:
                        st.session_state.user = response.user
                        initialize_chats(response.user)
                        st.success("Account created successfully!")
                        st.rerun()
                    else:
                        st.success("Account created. Please log in.")
                except Exception as error:
                    st.error(f"Registration failed: {error}")

    st.stop()

user_id = st.session_state.user.id

# Sidebar
with st.sidebar:
    st.title("📚 NotesMate")
    st.caption(f"Logged in as {st.session_state.user.email}")

    if st.button("＋ New Chat", use_container_width=True):
        try:
            new_chat = create_chat(supabase, user_id)
            st.session_state.chats[new_chat["id"]] = {
                "title": new_chat["title"],
                "messages": new_chat["messages"] or []
            }
            st.session_state.current_chat = new_chat["id"]
            st.rerun()
        except Exception as error:
            st.error(f"Could not create chat: {error}")

    st.divider()
    st.subheader("Chat History")

    for chat_id, chat in list(st.session_state.chats.items()):
        if st.button(
            chat["title"],
            key=f"chat_{chat_id}",
            use_container_width=True
        ):
            st.session_state.current_chat = chat_id
            st.rerun()

    st.divider()

    if st.button("🗑️ Delete Current Chat", use_container_width=True):
        try:
            chat_id = st.session_state.current_chat
            delete_chat(supabase, user_id, chat_id)
            del st.session_state.chats[chat_id]

            if not st.session_state.chats:
                new_chat = create_chat(supabase, user_id)
                st.session_state.chats[new_chat["id"]] = {
                    "title": new_chat["title"],
                    "messages": new_chat["messages"] or []
                }

            st.session_state.current_chat = next(iter(st.session_state.chats))
            st.success("Chat deleted.")
            st.rerun()
        except Exception as error:
            st.error(f"Could not delete chat: {error}")

    if st.button("Logout", use_container_width=True):
        try:
            logout_user(supabase)
        except Exception as error:
            st.warning(f"Logout warning: {error}")

        for key in ["user", "vector_store", "file_name", "chats", "current_chat"]:
            st.session_state.pop(key, None)

        st.rerun()

# Main dashboard
st.title("📚 NotesMate")
st.caption("Upload. Ask. Understand. Learn.")

st.subheader("📄 Upload Your Study Notes")

uploaded_file = st.file_uploader(
    "Upload PDF or Word documents",
    type=["pdf", "docx"]
)

if uploaded_file is not None:
    st.write(f"Selected file: **{uploaded_file.name}**")

    if st.button("Process My Notes"):
        try:
            with st.spinner("Reading and processing your notes..."):
                pages = extract_text(uploaded_file)

                if pages:
                    st.session_state.vector_store = create_study_assistant(
                        pages,
                        st.secrets["GEMINI_API_KEY"]
                    )
                    st.session_state.file_name = uploaded_file.name
                    st.success("Your notes are ready! Ask your questions below.")
                else:
                    st.warning("No readable text found in this document.")
        except Exception as error:
            st.error(f"Processing failed: {error}")

if st.session_state.file_name:
    st.success(f"Active notes: {st.session_state.file_name}")

st.divider()
st.subheader("💬 Ask Questions From Your Notes")

current_chat = st.session_state.chats[st.session_state.current_chat]

for message in current_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask anything about your study notes...")

if question:
    if st.session_state.vector_store is None:
        st.warning("Please upload and process your notes first.")
    else:
        current_chat["messages"].append({
            "role": "user",
            "content": question
        })

        if current_chat["title"] == "New Chat":
            current_chat["title"] = question[:35]

        try:
            save_chat(
                supabase,
                user_id,
                st.session_state.current_chat,
                current_chat["title"],
                current_chat["messages"]
            )
        except Exception as error:
            st.error(f"Could not save your question: {error}")

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("NotesMate is thinking..."):
                try:
                    answer = ask_question(
                        st.session_state.vector_store,
                        question,
                        st.secrets["GEMINI_API_KEY"]
                    )

                    st.markdown(answer)

                    current_chat["messages"].append({
                        "role": "assistant",
                        "content": answer
                    })

                    save_chat(
                        supabase,
                        user_id,
                        st.session_state.current_chat,
                        current_chat["title"],
                        current_chat["messages"]
                    )

                except Exception as error:
                    st.error(f"Unable to generate answer: {error}")
