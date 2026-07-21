import streamlit as st
import os, re
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.core.memory import ChatMemoryBuffer
from backend import NeuralSyncBackend  # Import our logic layer

# --- Initialization ---
backend = NeuralSyncBackend()
st.set_page_config(page_title="NeuralSync Pro", layout="wide", page_icon="🧠")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .transcript-card {
        background-color: #ffffff; padding: 20px; border-radius: 10px;
        border-left: 5px solid #ff4b4b; margin-top: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .quiz-box {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        border-left: 6px solid #00c6ff; margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .source-box {
        background-color: #f1f3f4; padding: 10px; border-radius: 5px;
        font-size: 0.85rem; border-left: 3px solid #6c757d; margin-bottom: 5px;
    }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- MODELS LOADER (CACHED FOR SPEED) ---
@st.cache_resource
def load_fixed_brain():
    # Forced to Llama 3.2 for better performance
    # Change this line in load_fixed_brain() function:
    return backend.load_models("llama3.2:1b")  

llm, embed_model = load_fixed_brain()

# --- States Initialization ---
for key in ["messages", "transcript", "index", "yt_docs", "query_engine", "source_type", "user_notes", "quiz_list", "important_qs"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key == "user_notes" else ([] if key in ["messages", "yt_docs", "quiz_list", "important_qs"] else None)

# --- Layout ---
col_src, col_chat, col_std = st.columns([1, 1.8, 1.2])

# --- 1. ENGINE SETTINGS & KNOWLEDGE (Left) ---
with col_src:
    st.markdown("###  Engine Status")
    st.info(" **Active Brain:** Llama 3.2 (Fixed)")
    
    st.divider()
    st.markdown("###  Knowledge Base")
    yt_disabled = (st.session_state.source_type == "pdf")
    with st.expander(" YouTube Link", expanded=(not yt_disabled)):
        yt_input = st.text_input("Paste Link", disabled=yt_disabled)
        if st.button("Import Video", disabled=yt_disabled) and yt_input:
            text = backend.fetch_yt_transcript(yt_input)
            if "Error" not in text:
                st.session_state.yt_docs = [Document(text=text)]
                st.session_state.source_type = "youtube"
                st.success("Video Synced!")
            else: st.error(text)

    pdf_disabled = (st.session_state.source_type == "youtube")
    st.markdown("#### PDF Upload")
    files = st.file_uploader("Upload Files", accept_multiple_files=True, disabled=pdf_disabled)
    if files: st.session_state.source_type = "pdf"

    if st.button(" Sync Neural Engine", type="primary"):
        with st.spinner("Booting Neural Engine..."):
            if not os.path.exists("./data"): os.makedirs("./data")
            if files:
                for f in files:
                    with open(os.path.join("./data", f.name), "wb") as b: b.write(f.getbuffer())
                docs = SimpleDirectoryReader("./data").load_data()
            else: docs = st.session_state.yt_docs
            
            if docs:
                st.session_state.index = VectorStoreIndex.from_documents(docs, embed_model=embed_model)
                memory = ChatMemoryBuffer.from_defaults(token_limit=4000)
                st.session_state.query_engine = st.session_state.index.as_chat_engine(
                    chat_mode="context",
                    memory=memory,
                    llm=llm,
                    system_prompt="You are NeuralSync AI running on Llama 3.2. Help accurately."
                )
                st.success("Neural Engine Ready!")
            else: st.error("Add a source first!")

# --- 2. CHAT & QUIZ (Middle) ---
with col_chat:
    tab_chat, tab_quiz, tab_imp = st.tabs([" Assistant", " Smart Quiz", " Important Qs"])    
    
    with tab_chat:
        st.markdown("### 🎙️ Llama 3.2 Assistant")
        audio_output = mic_recorder(start_prompt=" Record Question", stop_prompt=" Stop", key='voice_assistant')
        voice_query = backend.process_voice_to_text(audio_output) if audio_output else ""
        if voice_query: st.success(f"Recognized: {voice_query}")

        st.divider()
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): 
                st.markdown(msg["content"])
        
        text_prompt = st.chat_input("Ask anything...")
        final_query = text_prompt if text_prompt else voice_query

        if final_query:
            st.session_state.messages.append({"role": "user", "content": final_query})
            with st.chat_message("user"): st.markdown(final_query)
            
            if st.session_state.query_engine:
                with st.chat_message("assistant"):
                    with st.spinner("Llama is thinking..."):
                        response_obj = st.session_state.query_engine.chat(final_query)
                        source_texts = [n.node.get_content()[:300] + "..." for n in response_obj.source_nodes]
                        st.markdown(response_obj.response)
                        with st.expander(" Retrieval Transparency"):
                            for s in source_texts: st.markdown(f'<div class="source-box">{s}</div>', unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": response_obj.response, "sources": source_texts})
            else: st.warning("Sync IT")

    with tab_quiz:
        st.markdown("### Interactive Quiz Hub")
        if st.button(" Generate 5 MCQs"):
            if st.session_state.query_engine:
                with st.spinner("Generating Quiz..."):
                    res = st.session_state.query_engine.chat("Generate 5 MCQs. Format: QUESTION: (text) A) (opt) B) (opt) C) (opt) D) (opt) ANSWER: (Letter)")
                    st.session_state.quiz_list = backend.parse_quiz(res.response)
            else: st.warning("Sync source first!")
        
        for i, q in enumerate(st.session_state.quiz_list):
            st.markdown(f'<div class="quiz-box"><b>Q{i+1}: {q["q"]}</b></div>', unsafe_allow_html=True)
            choice = st.radio(f"Select Answer for Q{i+1}:", q["opts"], key=f"q_{i}")
            if st.button(f"Check Q{i+1}", key=f"btn_{i}"):
                if choice.strip().upper().startswith(q["correct"]): st.success("Correct! ")
                else: st.error(f"Incorrect. Correct answer is {q['correct']}")

    with tab_imp: 
        st.markdown("### AI Exam Predictor")
        if st.button(" Auto-Generate Key Questions"):
            if st.session_state.query_engine:
                with st.spinner("Analyzing priorities..."):
                    res = st.session_state.query_engine.chat("Identify 5 high-priority conceptual questions. Provide only questions.")
                    st.session_state.important_qs = backend.extract_important_qs(str(res.response))
            else: st.warning("First sync ")
    
        for q in st.session_state.important_qs:
            st.markdown(f'<div style="background-color: #fff4e5; padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; margin-bottom: 10px;">💡 {q}</div>', unsafe_allow_html=True)

# --- 3. STUDIO & EXPORTS (Right) ---
with col_std:
    st.markdown("###  Studio Settings")
    languages = {"English": "en", "Tamil": "ta", "Hindi": "hi", "Malayalam": "ml"}
    selected_lang_name = st.selectbox("Language:", list(languages.keys()))
    
    if st.button(" Reset All"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    st.markdown("###  Exports")
    if st.button(" Generate Report"):
        if st.session_state.query_engine:
            with st.spinner("Drafting PDF..."):
                res = st.session_state.query_engine.chat("Write a detailed professional report.")
                st.download_button(" Download PDF", backend.create_pdf_report(res.response), "Source_Report.pdf")

    if st.button(" Generate Slides"):
        if st.session_state.query_engine:
            with st.spinner("Designing Slides..."):
                res = st.session_state.query_engine.chat("Create 5 slides. Format: 'Slide Title: Slide Content'")
                st.download_button(" Download PPTX", backend.create_pptx(res.response), "Sidedeck.pptx")

    st.divider()
    st.session_state.user_notes = st.text_area("Draft ideas:", value=st.session_state.user_notes, height=100)

    if st.button(f" Generate {selected_lang_name} Audio"):
        if st.session_state.query_engine:
            with st.spinner("Generating..."):
                res = st.session_state.query_engine.chat(f"Summarize in {selected_lang_name}.")
                st.session_state.transcript = res.response
                gTTS(text=res.response, lang=languages[selected_lang_name]).save("audio_output.mp3")
                st.rerun()

    if st.session_state.transcript:
        st.markdown(f'<div class="transcript-card">{st.session_state.transcript}</div>', unsafe_allow_html=True)
    if os.path.exists("audio_output.mp3"): 
        st.audio("audio_output.mp3")