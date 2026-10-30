"""
Streamlit component for Multimodal Inputs and Outputs:
- Image Vision (upload image + prompt)
- Image Generation (DALL-E)
- Audio Transcription (Whisper)
- Text-to-Speech (TTS playback)
"""

import streamlit as st
import requests


def render_multimodal_tools(backend_url: str):
    """Render multimodal input and output panels in the sidebar or tabs."""
    st.subheader("🎨 Multimodal Tools")

    tool_choice = st.selectbox(
        "Select Multimodal Action:",
        ["🖼️ Image Vision", "✨ Generate Image", "🎙️ Audio Transcription", "🔊 Text-to-Speech"]
    )

    # 1. IMAGE VISION
    if tool_choice == "🖼️ Image Vision":
        st.write("Upload an image and ask the vision model about it.")
        uploaded_img = st.file_uploader("Upload Image:", type=["png", "jpg", "jpeg", "webp"], key="vision_uploader")
        if uploaded_img is not None:
            st.image(uploaded_img, caption="Preview", use_container_width=True)
            vision_prompt = st.text_input("Question about image:", value="Describe this image in detail.", key="vision_prompt")

            if st.button("👁️ Analyze Image", key="btn_analyze_img"):
                with st.spinner("Analyzing image..."):
                    try:
                        files = {"file": (uploaded_img.name, uploaded_img.getvalue(), uploaded_img.type)}
                        data = {"prompt": vision_prompt}
                        if st.session_state.get("conversation_id"):
                            data["conversation_id"] = st.session_state.conversation_id

                        resp = requests.post(f"{backend_url}/api/multimodal/vision", files=files, data=data, timeout=45)
                        if resp.status_code == 200:
                            res_data = resp.json()
                            if res_data.get("conversation_id"):
                                st.session_state.conversation_id = res_data["conversation_id"]

                            # Add to chat messages
                            st.session_state.messages.append({
                                "role": "user",
                                "content": vision_prompt,
                                "message_type": "image",
                                "media_url": res_data.get("image_url")
                            })
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": res_data["analysis"],
                                "message_type": "image",
                                "media_url": res_data.get("image_url")
                            })
                            st.success("Analysis complete! Added to chat.")
                            st.rerun()
                        else:
                            st.error(f"Analysis failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # 2. GENERATE IMAGE
    elif tool_choice == "✨ Generate Image":
        st.write("Generate an image using DALL-E.")
        img_prompt = st.text_area("Describe the image you want:", placeholder="e.g. A watercolor painting of an astronaut on a sunny beach", key="gen_img_prompt")
        if st.button("🎨 Create Image", key="btn_gen_image"):
            if not img_prompt.strip():
                st.warning("Please enter a description.")
            else:
                with st.spinner("Generating image..."):
                    try:
                        payload = {"prompt": img_prompt}
                        if st.session_state.get("conversation_id"):
                            payload["conversation_id"] = st.session_state.conversation_id

                        resp = requests.post(f"{backend_url}/api/multimodal/generate-image", json=payload, timeout=60)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success"):
                                st.success("Image generated!")
                                media_url = data.get("media_url")
                                full_url = f"{backend_url}{media_url}"
                                st.image(full_url, caption=img_prompt, use_container_width=True)

                                # Add to messages
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": f"Generate image: {img_prompt}",
                                    "message_type": "image"
                                })
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"Here is your generated image for: *{img_prompt}*",
                                    "message_type": "image",
                                    "media_url": media_url
                                })
                            else:
                                st.warning(data.get("message"))
                        else:
                            st.error(f"Request failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # 3. AUDIO TRANSCRIPTION & CHATBOT FLOW
    elif tool_choice == "🎙️ Audio Transcription":
        st.write("Upload an audio file (.mp3, .wav, .m4a, .ogg) to transcribe speech and query the chatbot.")
        audio_file = st.file_uploader("Upload Audio:", type=["mp3", "wav", "m4a", "ogg", "webm"], key="audio_uploader")

        if audio_file is not None:
            # If a new audio file is chosen, reset the transcript state
            if st.session_state.get("active_audio_filename") != audio_file.name:
                st.session_state["active_audio_filename"] = audio_file.name
                st.session_state["current_audio_transcript"] = None
                st.session_state["audio_transcript_submitted"] = False

            st.audio(audio_file)

            # Step 1: Transcribe Audio
            if st.button("📝 Transcribe Audio", key="btn_transcribe_audio"):
                with st.spinner("Transcribing spoken audio..."):
                    try:
                        files = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type or "audio/wav")}
                        resp = requests.post(f"{backend_url}/api/audio/transcribe", files=files, timeout=45)
                        if resp.status_code == 200:
                            data = resp.json()
                            raw_transcript = data.get("transcript", "")
                            if not raw_transcript or raw_transcript.strip().startswith("⚠️"):
                                st.warning(raw_transcript or "Audio transcription failed to produce any text.")
                                st.session_state["current_audio_transcript"] = None
                            else:
                                st.session_state["current_audio_transcript"] = raw_transcript
                                st.session_state["audio_transcript_submitted"] = False
                                st.rerun()
                        else:
                            err_detail = resp.json().get("detail", resp.text)
                            st.error(f"Transcription failed: {err_detail}")
                            st.session_state["current_audio_transcript"] = None
                    except Exception as e:
                        st.error(f"Error during transcription: {str(e)}")
                        st.session_state["current_audio_transcript"] = None

        # Step 2: If transcript exists, allow review/edit and submit to chatbot
        if st.session_state.get("current_audio_transcript"):
            st.success("✅ Transcription Complete!")
            transcript_text = st.text_area(
                "Review or edit transcript before asking chatbot:",
                value=st.session_state["current_audio_transcript"],
                key="audio_transcript_editor",
                height=120
            )

            send_clicked = st.button("💬 Ask Chatbot with Transcript", key="btn_send_transcript")

            if send_clicked:
                clean_text = transcript_text.strip()
                if not clean_text:
                    st.warning("Transcript is empty. Please enter some text.")
                elif (
                    st.session_state.get("audio_transcript_submitted")
                    and st.session_state.get("last_submitted_transcript") == clean_text
                ):
                    st.info("ℹ️ This transcript has already been sent to the chatbot.")
                else:
                    with st.spinner("Sending to chatbot and generating AI response..."):
                        try:
                            chat_payload = {
                                "conversation_id": st.session_state.get("conversation_id"),
                                "message": clean_text,
                                "mode": st.session_state.get("chat_mode", "chat")
                            }
                            resp = requests.post(
                                f"{backend_url}/api/chat/message",
                                json=chat_payload,
                                timeout=60
                            )
                            if resp.status_code == 200:
                                chat_data = resp.json()
                                st.session_state.conversation_id = chat_data["conversation_id"]
                                st.session_state["audio_transcript_submitted"] = True
                                st.session_state["last_submitted_transcript"] = clean_text

                                # Append both turns to session conversation history
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": clean_text,
                                    "message_type": "audio"
                                })
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": chat_data["content"],
                                    "message_type": "text"
                                })

                                st.success("🎉 Response received and added to conversation history!")
                                with st.chat_message("assistant", avatar="🤖"):
                                    st.markdown(chat_data["content"])
                            else:
                                err_msg = resp.json().get("detail", resp.text)
                                st.error(f"⚠️ Chatbot response generation failed: {err_msg}")
                        except Exception as e:
                            st.error(f"⚠️ Connection error while sending to chatbot: {str(e)}")

    # 4. TEXT-TO-SPEECH
    elif tool_choice == "🔊 Text-to-Speech":
        st.write("Convert any text into spoken audio.")
        tts_text = st.text_area("Enter text to synthesize:", placeholder="Type a message or paste text to hear it spoken aloud...", key="tts_input_text")
        tts_voice = st.selectbox("Voice:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"], key="tts_voice")

        if st.button("🎧 Generate Speech", key="btn_run_tts"):
            if not tts_text.strip():
                st.warning("Please enter some text.")
            else:
                with st.spinner("Synthesizing audio..."):
                    try:
                        resp = requests.post(
                            f"{backend_url}/api/audio/tts",
                            json={"text": tts_text, "voice": tts_voice},
                            timeout=30
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success") and data.get("audio_url"):
                                audio_url = f"{backend_url}{data['audio_url']}"
                                st.success(f"Generated via {data.get('provider', 'TTS')}:")
                                st.audio(audio_url)
                            else:
                                st.warning(data.get("message"))
                        else:
                            st.error(f"TTS request failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

