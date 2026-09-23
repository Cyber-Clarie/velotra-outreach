# Velotra Creator Outreach OS

A local-first CRM and outreach management system built for managing creator relationships, outreach campaigns, conversations, follow-ups, and AI-assisted replies.

Built with Python, Flask, SQLite, and Ollama.

## 🚀 Features

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
