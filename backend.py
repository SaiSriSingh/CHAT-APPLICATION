from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import uuid
import webbrowser
import threading

app = FastAPI()

# Serve static files (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Manage active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        client_id = str(uuid.uuid4())[:8]
        self.active_connections[client_id] = websocket
        return client_id

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def broadcast(self, message: str, sender_id: str = None):
        for client_id, connection in self.active_connections.items():
            prefix = "You" if client_id == sender_id else f"User {sender_id or 'System'}"
            await connection.send_text(f"{prefix}: {message}")

# Create instance of manager
manager = ConnectionManager()

# Simple rule-based chatbot logic
def chatbot_response(user_msg: str) -> str:
    msg = user_msg.lower().strip()

    if "hello" in msg or "hi" in msg:
        return "Hey there! 👋 How can I help you today?"
    elif "how are you" in msg:
        return "I'm just a bunch of Python code, but I'm running great!"
    elif "your name" in msg:
        return "I'm CodTech ChatBot 🤖"
    elif "bye" in msg or "goodbye" in msg:
        return "Goodbye! Have a great day ahead! 👋"
    elif "help" in msg:
        return "Sure! Ask me anything about this chat app, coding, or tech."
    else:
        return "Hmm... I'm still learning. Try asking something else!"

# Optional root endpoint
@app.get("/")
async def get():
    return HTMLResponse("""
    <html><body><h2>Go to <a href='/static/chat.html'>/static/chat.html</a> to use the chat</h2></body></html>
    """)

# WebSocket chat logic
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    client_id = await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, sender_id=client_id)

            # Bot response
            bot_reply = chatbot_response(data)
            await manager.broadcast(bot_reply, sender_id="Bot")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast(f"User {client_id} left the chat", sender_id="System")

# Start the app
if __name__ == "__main__":
    def open_browser():
        	webbrowser.open("http://127.0.0.1:8000/static/chat.html")

    threading.Timer(1.5, open_browser).start()

    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
