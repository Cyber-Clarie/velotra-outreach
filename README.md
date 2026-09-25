# Velotra Creator Outreach OS

A local-first CRM and outreach management system built for managing creator relationships, outreach campaigns, conversations, follow-ups, and AI-assisted replies.

Built with Python, Flask, SQLite, and Ollama.

 🚀 Features

- Creator CRM
- Bulk creator import
- Instagram URL import
- Duplicate detection
- New creator & reactivation tracking
- Outreach action queue
- Follow-up scheduling
- Overdue / due / upcoming actions
- Creator conversation history
- Inbound & outbound message tracking
- AI-assisted reply generation
- Human approval before AI replies are sent
- Local Ollama integration
- Velotra product knowledge base
- Knowledge-aware AI responses
- Creator status management
- Local SQLite database
- Works without paid AI APIs

## 🧠 AI

The system uses Ollama for local AI inference.

AI can:

- Understand incoming creator messages
- Generate suggested replies
- Identify conversation intent
- Suggest creator status changes
- Determine whether a follow-up is required
- Use Velotra's internal knowledge base
- Avoid inventing information when the knowledge base doesn't contain an answer

AI-generated replies remain **human-reviewed** before sending.

## 🏗️ Architecture

```text
Flask Web App
      │
      ├── Creator CRM
      │
      ├── Message System
      │
      ├── Action Queue
      │
      ├── Follow-up Engine
      │
      ├── AI Service
      │       │
      │       └── Ollama
      │
      ├── Knowledge System
      │
      └── SQLite Database
🛠️ Tech Stack
- Python
- Flask
- SQLite
- Ollama
- Llama 3.1
- HTML
- CSS
- JavaScript
- Git / GitHub
📁 Project Structure
velotra-outreach/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
│
├── database/
│
├── services/
│   ├── ai_service.py
│   ├── conversation_service.py
│   ├── followup_service.py
│   ├── import_service.py
│   ├── knowledge_service.py
│   └── outreach_service.py
│
├── knowledge/
│   └── velotra.json
│
├── templates/
│
├── static/
│
└── tests/
⚙️ Setup
1. Clone
git clone https://github.com/Cyber-Clarie/velotra-outreach.git
cd velotra-outreach
2. Create virtual environment
python -m venv venv
3. Activate
Windows:
venv\Scripts\activate
4. Install dependencies
pip install -r requirements.txt
5. Install Ollama
Install Ollama and pull a local model:
ollama pull llama3.1
6. Run the application
python app.py
Open:
http://127.0.0.1:5000
🔐 Environment Variables
Create a .env file:
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
🧪 Testing
Run:
pytest
The project includes tests for:
- Creator import
- Duplicate detection
- Action queue
- Follow-ups
- Conversations
- AI responses
- Knowledge retrieval
- Reactivation workflow
- End-to-end workflows
📌 Current Status
The CRM, action queue, conversation system, local AI integration, and knowledge system are implemented.
Instagram messaging integration is intentionally kept separate and is not included in the current local CRM implementation.
🎯 Why I Built This
I wanted to build a real system instead of another tutorial project.
The goal was to solve a practical problem:
How can creator outreach be organized into one system instead of managing creators, messages, follow-ups, and AI assistance manually?

This project is also part of my journey into backend development, automation, AI engineering, and cybersecurity.
👨‍💻 Author
Built by Clarie
GitHub:
https://github.com/Cyber-Clarie

---

## 2. Push it to GitHub

From the project folder:

```bash
git add .
git commit -m "Redesign CRM frontend and update documentation"
git push origin main
