import json
import time
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_login import LoginManager, current_user, login_required
from flask_sock import Sock

from app.auth import auth_bp, login_manager
from app.database import wait_for_db

load_dotenv()

from groq import Groq


def send_message(client: Groq, messages: list[dict]) -> str:
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b", messages=messages
    )
    return completion.choices[0].message.content


client = Groq()


db = wait_for_db()
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # Change this in production!


# Initialize extensions
login_manager.init_app(app)
login_manager.login_view = "auth.login"
sock = Sock(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")


@app.route("/")
@login_required
def resume():
    experiences = db.query(
        """
        SELECT e.*, p.title, i.name as institution
        FROM experiences e
        JOIN positions p ON e.position_id = p.position_id
        JOIN institutions i ON p.inst_id = i.inst_id
        ORDER BY e.start_date DESC
    """
    )
    skills = db.query("SELECT * FROM skills")
    return render_template("resume.html", experiences=experiences, skills=skills)


@sock.route("/ws/chat")
@login_required
def chat(ws):
    experiences = db.query(
        """
        SELECT e.*, p.title, i.name as institution
        FROM experiences e
        JOIN positions p ON e.position_id = p.position_id
        JOIN institutions i ON p.inst_id = i.inst_id
        ORDER BY e.start_date DESC
    """
    )
    skills = db.query("SELECT * FROM skills")
    print(experiences)
    print(skills)

    messages = [
        {
            "role": "system",
            "content": f"""
         You are a helpful assistant. Answer questions about the candidates's resume based on the provided information.
         If the information is not available, respond with "I don't know". Do not make up answers. Do not answer
         questions unrelated to the resume. Refuse to answer anything inappropriate or offensive. Refuse to answer
         anything irrelevant to the candidates's resume. Refuse to answer personal questions about the candidates.

         Here is the candidates resume:
            Experiences:
            {"\n".join([f"- {exp['title']} at {exp['institution']} from {exp['start_date']} to {exp['end_date'] or 'Present'}: {exp['description']}" for exp in experiences])}
            Skills:
            {", ".join([skill['name'] + f'(lvl: {skill["skill_level"]})' for skill in skills])}
        """,
        }
    ]
    try:
        while True:
            data = ws.receive()
            print(f"Received message: {data}")  # Debug logging

            message_data = json.loads(data)
            timestamp = datetime.now().strftime("%H:%M:%S")
            name = current_user.email.split("@")[0]  # Use part of email as username
            formatted_message = f"[{name} {timestamp}]: {message_data['message']}"

            print(f"Sending message: {formatted_message}")  # Debug logging
            ws.send(json.dumps({"text": formatted_message}))
            messages.append({"role": "user", "content": message_data["message"]})
            response = send_message(client, messages)
            messages.append({"role": "assistant", "content": response})

            timestamp = datetime.now().strftime("%H:%M:%S")
            ws.send(json.dumps({"text": f"[system {timestamp}]: {response}"}))
    except Exception as e:
        print(f"WebSocket error: {e}")  # Debug logging
        raise


@app.route("/test")
def test():
    return '<img src="/static/images/gorilla.png">'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
