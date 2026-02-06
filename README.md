# 📦 Customer Support Chatbot (FastAPI + React + Rasa + PostgreSQL)
A full-stack customer support chatbot system built with:

- 🧠 Rasa 3.x (intent classification + entity extraction)
- ⚙️ FastAPI backend (conversation logic + database + hybrid NLP)
- 🌐 React + Vite frontend + Tailwind CSS (chat UI)
- 🗄️ PostgreSQL for storing users, messages & conversations
- 🐳 Docker & Docker Compose 

This project is designed for academic purposes (FYP/CSIT321) but follows real-world architecture and production-grade practices.

# 🌐 Hosting & Deployment
This project is containerized and ready for cloud deployment.
- Hosting Platform: [frontend: Vercel], [backend: Render], [Database: Neon Tech], [rasa server and action server: Google Cloud Run]
- Orchestration: Docker Compose
- Web Server: Nginx (serving the React build and reverse-proxying API requests)
- Database: Managed PostgreSQL

# Access Point
- https://chatbot-frontend-ten-pink.vercel.app/

# 🚀 Features
🤖 Chatbot Intelligence
- Rasa NLU for intent recognition & entity extraction
- Backend hybrid logic for:
- Order tracking
- Product inquiries
- Returns & policies
- General FAQs

# 🧩 Backend (FastAPI)
- Stores conversations & messages
- Handles intents and replies
- Integrates with Rasa via API
- Provides quick replies
- REST API with OpenAPI docs (/docs)

# 💬 Frontend (React + Vite)
- Clean chat interface
- Typing indicator
- Quick reply buttons
- Conversation state handling
- Backend + Rasa integration

# 📚 Database Schema
- Users: Manages customer identities.
- Conversations: Tracks unique chat sessions.
- Messages: Stores the full dialogue history with edit tracking.
- Orders: Simulated retail data for intent fulfillment.
- Chat Logs: Performance metrics (Intent accuracy, Response time).

# 🛠️ Technologies Used
- FastAPI
- React + Vite + Tailwind CSS
- Rasa 3.6
- PostgreSQL
- SQLAlchemy
- Docker
- Nginx

# 📚 Future Improvements
- JWT authentication
- Admin dashboard
- Multi-language support
- Vector search for FAQ (OpenAI embeddings)
- Real-time websocket chat
