"""
Streamlit Chat UI rendering helpers: message cards, citations, and media.
"""

import streamlit as st


def render_message(msg: dict, backend_url: str):
    """Render a single message with role avatar, text, media, and source citations."""
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    sources = msg.get("sources")
    media_url = msg.get("media_url")
    msg_type = msg.get("message_type", "text")

    avatar = "🧑" if role == "user" else "🤖"
    if msg_type == "emotional":
        avatar = "🌿"
    elif msg_type == "search":
        avatar = "🔍"
    elif msg_type == "rag":
        avatar = "📚"

    with st.chat_message(role, avatar=avatar):
        # Render main text
        st.markdown(content)

        # Render media if present (image preview or audio player)
        if media_url:
            full_media_url = media_url if media_url.startswith("http") else f"{backend_url}{media_url}"
            if msg_type == "image" or media_url.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                st.image(full_media_url, caption="Generated / Attached Image", use_container_width=True)
            elif msg_type == "audio" or media_url.lower().endswith((".mp3", ".wav", ".ogg")):
                st.audio(full_media_url)

        # Render source citations if present
        if sources and len(sources) > 0:
            with st.expander(f"📑 Sources & Citations ({len(sources)})", expanded=False):
                for idx, src in enumerate(sources, 1):
                    title = src.get("title", f"Source #{idx}")
                    url = src.get("url")
                    snippet = src.get("snippet", "")
                    date = src.get("date")

                    if url:
                        st.markdown(f"**{idx}. [{title}]({url})**" + (f" *({date})*" if date else ""))
                    else:
                        st.markdown(f"**{idx}. {title}**")

                    if snippet:
                        st.caption(f"> {snippet}")

