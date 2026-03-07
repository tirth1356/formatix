Backend
cd backend
pip install -r requirements.txt (Python 3.10/3.11 if 3.13 has build issues)
Copy .env.example to .env
ollama pull phi3 and ollama pull llama3
uvicorn main:app --reload --host 0.0.0.0 --port 8000


Frontend
cd frontend
npm install
Copy .env.local.example to .env.local (default NEXT_PUBLIC_API_LOCAL=http://localhost:8000)
npm run dev → http://localhost:3000