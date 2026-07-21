Ithu **human-typed format** (oru developer oda **Personal Notes & Project Pitch** style-la):

---

# 🧠 NeuralSync Pro (NOTE-MAX)

Hey! This is my personal project called **NeuralSync Pro**. It’s basically a local AI study assistant that takes long YouTube videos or messy PDF notes and turns them into something actually useful—like summaries, quizzes, audio notes, and presentation slides.

The best part? It runs **100% locally on your own machine** using Ollama (Llama 3.2). No paid API keys, no subscriptions, and complete privacy for your documents.

---

## 🔥 What can it do?

* **Smart Chat (RAG):** Upload a PDF or paste a YouTube link, and start asking questions right away.
* **Voice Questions:** Don't feel like typing? Just hit the mic button and ask your question out loud.
* **Instant Quizzes:** Automatically creates 5 multiple-choice questions from your study material with built-in answer validation.
* **Exam Predictor:** Pulls out high-priority core conceptual questions that are likely to show up in exams.
* **Audio Summaries:** Generates spoken audio notes in English, Tamil, Hindi, or Malayalam using gTTS.
* **One-Click Exports:** Converts notes into clean downloadable PDFs or ready-to-present PPTX slide decks.
* **Retrieval Transparency:** Lets you see the exact chunks of text the AI used to answer your query.

---

## 🛠️ Tech Stack & Tools

* **UI:** Streamlit (with custom CSS tweaks for a SaaS-like look)
* **AI Orchestration & RAG:** LlamaIndex (with `ChatMemoryBuffer` for short-term chat context)
* **Local Model:** Ollama running `llama3.2:1b` (or `llama3.2`)
* **Embeddings:** HuggingFace `BAAI/bge-small-en-v1.5`
* **File & Audio Utils:** `youtube-transcript-api`, `fpdf`, `python-pptx`, `gTTS`, `speech_recognition`

---

## 🚀 How to set it up locally

### Step 1: Set up Ollama

First, make sure Ollama is installed on your system. Open terminal and run:

```bash
ollama pull llama3.2:1b
ollama serve

```

### Step 2: Clone & Install Dependencies

Clone this repo and install all required Python packages:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
pip install -r requirements.txt

```

### Step 3: Run the application

Start the Streamlit interface:

```bash
streamlit run frontend.py

```

---

## 📂 Project Structure

```text
├── backend.py          # Core logic (Ollama setup, TTS, PDF/PPTX exporters)
├── frontend.py         # Streamlit UI, chat, audio recorder, and tabs
├── requirements.txt    # Python packages list
├── .gitignore          # Prevents temp files, MP3s, and PDFs from uploading
└── README.md           # Documentation

```
