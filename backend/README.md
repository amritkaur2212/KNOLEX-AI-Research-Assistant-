
# Knolex – Ask. Analyze. Discover.

An AI-powered Research Assistant Platform with intelligent document analysis and an AI Writing Studio.

## About the Project

Knolex is an AI-powered platform designed to simplify academic research, document analysis, information discovery, and content creation.

It combines Retrieval-Augmented Generation (RAG) with AI-assisted writing capabilities to provide an integrated workspace for students and researchers.

## Key Features

- **AI Research Assistant:** Ask questions about uploaded PDF documents.
- **PDF Processing:** Extract and process text from research documents.
- **RAG-based Question Answering:** Retrieve relevant document information and generate contextual responses.
- **AI Writing Studio:** Assist with drafting, refining, and improving written content.
- **Intelligent Document Search:** Find relevant information from processed documents.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | API development |
| Google Gemini AI | AI-powered responses |
| LangChain | LLM integration |
| ChromaDB | Vector database |
| Embeddings | Semantic document search |
| HTML, CSS, JavaScript | Frontend development |
| PyMuPDF | PDF text extraction |

## Project Structure

```text
Knolex/
├── backend/
│   ├── app.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── pdf_reader.py
│   ├── vector_store.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .gitignore
└── README.md
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/amritkaur2212/KNOLEX-AI-Research-Assistant-.git
```

2. Navigate to the project directory.

3. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

4. Configure your Google Gemini API key in a local `.env` file inside the backend folder.

5. Start the FastAPI application using your configured backend entry point.

## Project Objective

To make academic research and writing more efficient through AI-powered document understanding, intelligent question answering, and writing assistance.

## Developer

Developed as a Final Year Major Project.

**Knolex – Ask. Analyze. Discover.**
