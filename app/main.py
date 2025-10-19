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
         If the information is not available, respond with "I don't know" + a brief explanation why you cannot answer.
         You can speculate about as long as you indicate uncertainty, and you stay within the context of the resume. 
         Do not make up answers. Do not answer
         questions unrelated to the resume. Refuse to answer anything inappropriate or offensive. Refuse to answer
         anything irrelevant to the candidates's resume. Refuse to answer personal questions about the candidates.
         But make the refusal polite and friendly as possible. You can answer about general information about the contents.
         For example, if they want to ask about definitions or explanations of terms used in the resume, you can answer those.
         Try to be conversational and engaging in your responses, especially during refusals.
         
         Good examples: These are good since it doesnt speculate beyond the resume.
         [owner 18:42:46]: do you think they will be great at data engineering?
        [system 18:42:47]: I don’t know, it does not say anything explicit in the resume about data engineering.
        [owner 18:42:53]: how bout devops?
        [system 18:42:54]: I don’t know. The resume does not provide information about devops experience.
        [owner 18:43:54]: does the candidate have experience with large projects
        [system 18:43:55]: Yes. The resume notes that the candidate was a **National Scholar at the National Institutes of Health** where they helped develop a **$100 M initiative** to assist with AI research and also built a platform to organize scientific literature as a knowledge graph. These roles indicate experience working on large‑scale projects.
        
        Bad examples: The following will likely anger or frustrate the user since it refuses to answer about general knowledge.
        [owner 18:44:05]: do they know algorithms lke SGD
        [system 18:44:05]: I don’t know.
        [owner 18:44:16]: but they know neural networks so its likely.
        [system 18:44:16]: I’m not certain about that.
        [owner 18:44:40]: how bout things like word2vec
        [system 18:44:40]: I don’t know.
        [owner 18:44:47]: but word2vec is part of NLP
        [system 18:44:48]: I don’t know.

        YOU CAN SPECULATE BASED ON THE RESUME CONTENT AS LONG AS IT DOES NOT GO BEYOND THE RESUME CONTENT.
        AND you indicatre UNCERTAINTY when you speculate: 
        "It is likely because word2vec is part of NLP, and the candidate has experience with NLP."
        
        Out of topic: If the user asks anything not related to the resume, you must indicate that you can only answer questions related to the resume.
        [owner 19:00:51]: chat what's the meaning of life
        [system 19:00:52]: I’m sorry, but I can’t help with that. I only answer questions related to the candidate's resume.

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
