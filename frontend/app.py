"""
Streamlit Frontend for the Multimodal AI Chatbot.
Provides an interactive, beginner-friendly UI supporting:
- Multimodal Input (Text, Vision Images, Documents, Spoken Audio)
- Multimodal Output (Text, Speech Audio Player, Generated Images)
- Document RAG with semantic retrieval and citations
- Live Web Search with source verification
- Document Knowledge Base Management (Create, View, Edit, Download, Delete)
- Personal Emotional Assistance with safety boundaries
"""

import os
import streamlit as st
import requests

from frontend.components.chat_ui import render_message
from frontend.components.settings_ui import render_system_status
from frontend.components.documents_ui import render_documents_manager
from frontend.components.multimodal_ui import render_multimodal_tools

# Page setup
st.set_page_config(
    page_title="Multimodal AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Initialize Session State
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "chat"  # 'chat', 'rag', 'search', 'emotional'


def clear_current_chat():
    """Reset session state messages and clear conversation on backend if one exists."""
    if st.session_state.conversation_id:
        try:
            requests.delete(
                f"{BACKEND_URL}/api/chat/conversations/{st.session_state.conversation_id}/messages",
                timeout=3
            )
        except Exception:
            pass
    st.session_state.messages = []
    st.session_state.conversation_id = None
    st.rerun()


# --- Sidebar Navigation & Controls ---
with st.sidebar:
    st.title("🤖 AI Control Center")
    render_system_status(BACKEND_URL)
    st.divider()

    st.subheader("🎯 Conversation Mode")
    mode_options = {
        "chat": "💬 Standard Chat",
        "rag": "📚 Document RAG",
        "search": "🌐 Web Search",
        "emotional": "🌿 Emotional Support"
    }

    selected_mode = st.radio(
        "Choose Mode:",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=list(mode_options.keys()).index(st.session_state.chat_mode)
    )
    if selected_mode != st.session_state.chat_mode:
        st.session_state.chat_mode = selected_mode
        st.rerun()

    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        clear_current_chat()

    st.caption("Multimodal AI Chatbot • FastAPI + Streamlit + PostgreSQL")


# --- Main Application Area: Navigation Tabs ---
main_tab_chat, main_tab_docs, main_tab_tools = st.tabs([
    "💬 Chat Hub",
    "📚 Document Management",
    "🎨 Multimodal Studio"
])

# ==========================================
# TAB 1: CONVERSATIONAL CHAT HUB
# ==========================================
with main_tab_chat:
    mode_headers = {
        "chat": ("💬 General AI Chatbot", "Ask any question, discuss code, brainstorm, or explore ideas."),
        "rag": ("📚 Document Grounded RAG", "Ask questions strictly grounded in your indexed documents with source citations."),
        "search": ("🌐 Live Web Search", "Get up-to-date answers grounded in real-time web results with source links."),
        "emotional": ("🌿 Personal Emotional Assistance", "A safe, supportive, empathetic space to express feelings, reflect, and practice grounding.")
    }

    header_title, header_desc = mode_headers.get(st.session_state.chat_mode, ("Multimodal AI", ""))
    st.header(header_title)
    st.caption(header_desc)

    # Render Active Chat Message History
    if not st.session_state.messages:
        st.info("👋 Welcome! Start typing below, upload a document in **Document Management**, or explore **Multimodal Studio**.")
    else:
        for msg in st.session_state.messages:
            render_message(msg, BACKEND_URL)

    # Listen to last assistant reply with TTS
    if st.session_state.messages:
        last_msg = st.session_state.messages[-1]
        if last_msg.get("role") == "assistant" and last_msg.get("content"):
            col_tts, _ = st.columns([1, 4])
            with col_tts:
                if st.button("🔊 Listen to Answer", key="btn_read_last_answer"):
                    with st.spinner("Generating speech audio..."):
                        try:
                            tts_resp = requests.post(
                                f"{BACKEND_URL}/api/audio/tts",
                                json={"text": last_msg["content"][:2000], "voice": "alloy"},
                                timeout=20
                            )
                            if tts_resp.status_code == 200:
                                tts_data = tts_resp.json()
                                if tts_data.get("audio_url"):
                                    st.audio(f"{BACKEND_URL}{tts_data['audio_url']}")
                        except Exception as e:
                            st.warning(f"Audio playback error: {str(e)}")

    # User Input Field
    user_input = st.chat_input(f"Type your message for {mode_options[st.session_state.chat_mode]}...")

    if user_input and user_input.strip():
        cleaned_input = user_input.strip()

        # 1. Add user message to session state
        user_msg_item = {
            "role": "user",
            "content": cleaned_input,
            "message_type": st.session_state.chat_mode
        }
        st.session_state.messages.append(user_msg_item)
        render_message(user_msg_item, BACKEND_URL)

        # 2. Call Mode-Specific Endpoint
        with st.spinner("Thinking..."):
            try:
                # MODE: RAG
                if st.session_state.chat_mode == "rag":
                    rag_payload = {
                        "query": cleaned_input,
                        "conversation_id": st.session_state.conversation_id,
                        "top_k": 4,
                        "similarity_threshold": 0.20
                    }
                    resp = requests.post(f"{BACKEND_URL}/api/rag/query", json=rag_payload, timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.conversation_id = data.get("conversation_id", st.session_state.conversation_id)
                        asst_msg = {
                            "role": "assistant",
                            "content": data["answer"],
                            "message_type": "rag",
                            "sources": data.get("sources")
                        }
                        st.session_state.messages.append(asst_msg)
                        render_message(asst_msg, BACKEND_URL)
                    else:
                        st.error(f"RAG query failed: {resp.text}")

                # MODE: WEB SEARCH
                elif st.session_state.chat_mode == "search":
                    search_payload = {
                        "query": cleaned_input,
                        "conversation_id": st.session_state.conversation_id,
                        "max_results": 5
                    }
                    resp = requests.post(f"{BACKEND_URL}/api/search/query", json=search_payload, timeout=45)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.conversation_id = data.get("conversation_id", st.session_state.conversation_id)
                        asst_msg = {
                            "role": "assistant",
                            "content": data["answer"],
                            "message_type": "search",
                            "sources": data.get("sources")
                        }
                        st.session_state.messages.append(asst_msg)
                        render_message(asst_msg, BACKEND_URL)
                    else:
                        st.error(f"Web search failed: {resp.text}")

                # MODE: EMOTIONAL SUPPORT
                elif st.session_state.chat_mode == "emotional":
                    emo_payload = {
                        "message": cleaned_input,
                        "conversation_id": st.session_state.conversation_id
                    }
                    resp = requests.post(f"{BACKEND_URL}/api/emotional/respond", json=emo_payload, timeout=45)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.conversation_id = data.get("conversation_id", st.session_state.conversation_id)
                        asst_msg = {
                            "role": "assistant",
                            "content": data["response"],
                            "message_type": "emotional"
                        }
                        st.session_state.messages.append(asst_msg)
                        render_message(asst_msg, BACKEND_URL)
                    else:
                        st.error(f"Emotional support failed: {resp.text}")

                # MODE: STANDARD CHAT
                else:
                    chat_payload = {
                        "conversation_id": st.session_state.conversation_id,
                        "message": cleaned_input,
                        "mode": "chat"
                    }
                    resp = requests.post(f"{BACKEND_URL}/api/chat/message", json=chat_payload, timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.conversation_id = data["conversation_id"]
                        asst_msg = {
                            "role": "assistant",
                            "content": data["content"],
                            "message_type": "text"
                        }
                        st.session_state.messages.append(asst_msg)
                        render_message(asst_msg, BACKEND_URL)
                    else:
                        st.error(f"Chat request failed: {resp.text}")

            except requests.exceptions.ConnectionError:
                st.error("🔴 Unable to connect to the backend API. Please make sure the FastAPI server is running on http://127.0.0.1:8000.")
            except Exception as e:
                st.error(f"⚠️ Error: {str(e)}")

# ==========================================
# TAB 2: DOCUMENT MANAGEMENT
# ==========================================
with main_tab_docs:
    render_documents_manager(BACKEND_URL)

# ==========================================
# TAB 3: MULTIMODAL STUDIO
# ==========================================
with main_tab_tools:
    render_multimodal_tools(BACKEND_URL)
