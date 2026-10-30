"""
Streamlit component for Document Management:
- Create new text document
- Upload documents (.pdf, .txt, .docx, .md)
- List, view, edit, download, and delete documents
"""

import streamlit as st
import requests


def render_documents_manager(backend_url: str):
    """Render the full document management UI in an expander or tab."""
    st.subheader("📚 Document Knowledge Base")
    st.caption("Upload or author documents to ground AI responses in your knowledge.")

    tab_list, tab_upload, tab_create = st.tabs(["📂 Browse & Edit", "📤 Upload File", "✍️ Create Document"])

    # 1. BROWSE & EDIT DOCUMENTS
    with tab_list:
        try:
            resp = requests.get(f"{backend_url}/api/documents", timeout=5)
            if resp.status_code == 200:
                docs = resp.json()
                if not docs:
                    st.info("No documents stored yet. Upload a file or create a text document below!")
                else:
                    doc_titles = {f"{d['title']} ({d['file_type'].upper()} | {d['chunks_count']} chunks)": d["id"] for d in docs}
                    selected_title = st.selectbox("Select Document:", list(doc_titles.keys()))
                    selected_id = doc_titles[selected_title]

                    # Fetch selected document details
                    doc_resp = requests.get(f"{backend_url}/api/documents/{selected_id}", timeout=5)
                    if doc_resp.status_code == 200:
                        doc_data = doc_resp.json()
                        st.write(f"**Size:** {doc_data['file_size_bytes']} bytes | **Indexed Chunks:** {doc_data['chunks_count']}")

                        # Editable content area
                        with st.form(key=f"edit_form_{selected_id}"):
                            edit_title = st.text_input("Title:", value=doc_data["title"])
                            edit_content = st.text_area("Content:", value=doc_data["content"], height=250)
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                save_submitted = st.form_submit_button("💾 Save & Re-index", use_container_width=True)

                        if save_submitted:
                            up_resp = requests.put(
                                f"{backend_url}/api/documents/{selected_id}",
                                json={"title": edit_title, "content": edit_content},
                                timeout=10
                            )
                            if up_resp.status_code == 200:
                                st.success("Document updated and RAG index refreshed!")
                                st.rerun()
                            else:
                                st.error("Failed to update document.")

                        col_dl, col_del = st.columns([1, 1])
                        with col_dl:
                            # Download link
                            dl_url = f"{backend_url}/api/documents/{selected_id}/download"
                            st.link_button("⬇️ Download Document", dl_url, use_container_width=True)

                        with col_del:
                            if st.button("🗑️ Delete Document", key=f"del_{selected_id}", use_container_width=True):
                                del_resp = requests.delete(f"{backend_url}/api/documents/{selected_id}", timeout=5)
                                if del_resp.status_code == 200:
                                    st.warning(f"Deleted '{doc_data['title']}' and cleared its chunks.")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete document.")
            else:
                st.error("Failed to fetch documents from server.")
        except Exception as e:
            st.error(f"Error connecting to documents API: {str(e)}")

    # 2. UPLOAD FILE
    with tab_upload:
        st.write("Upload a PDF, TXT, MD, or DOCX document (Max: 10MB).")
        uploaded_file = st.file_uploader(
            "Choose file:",
            type=["txt", "md", "pdf", "docx"],
            key="doc_file_uploader"
        )
        if uploaded_file is not None:
            st.info(f"Selected: **{uploaded_file.name}** ({uploaded_file.size} bytes)")
            if st.button("🚀 Upload & Index Document", key="btn_upload_doc"):
                with st.spinner("Extracting text and generating RAG embeddings..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        up_resp = requests.post(f"{backend_url}/api/documents/upload", files=files, timeout=30)
                        if up_resp.status_code == 201:
                            res_data = up_resp.json()
                            st.success(f"Successfully uploaded and indexed '{res_data['title']}' ({res_data['chunks_count']} chunks)!")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {up_resp.json().get('detail', up_resp.text)}")
                    except Exception as e:
                        st.error(f"Upload error: {str(e)}")

    # 3. CREATE NEW TEXT DOCUMENT
    with tab_create:
        with st.form(key="create_doc_form"):
            new_title = st.text_input("Document Title:", placeholder="e.g. Project Architecture Notes")
            new_type = st.selectbox("Format:", ["txt", "md"])
            new_content = st.text_area("Document Content:", placeholder="Write or paste your text here...", height=200)
            create_submitted = st.form_submit_button("✨ Create & Index Document", use_container_width=True)

            if create_submitted:
                if not new_title.strip() or not new_content.strip():
                    st.warning("Please provide both a title and content.")
                else:
                    try:
                        c_resp = requests.post(
                            f"{backend_url}/api/documents",
                            json={"title": new_title, "content": new_content, "file_type": new_type},
                            timeout=15
                        )
                        if c_resp.status_code == 201:
                            res_data = c_resp.json()
                            st.success(f"Created document '{res_data['title']}' with {res_data['chunks_count']} chunks indexed!")
                            st.rerun()
                        else:
                            st.error(f"Creation failed: {c_resp.json().get('detail', c_resp.text)}")
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")

