import time
import json
from flask import Flask, jsonify, render_template
from app.database import wait_for_db
from app.auth import auth_bp, login_manager
from flask_sock import Sock
from flask_login import LoginManager, login_required, current_user
from datetime import datetime

db = wait_for_db()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production!


# Initialize extensions
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
sock = Sock(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')



@app.route('/')
@login_required
def resume():
    experiences = db.query("""
        SELECT e.*, p.title, i.name as institution
        FROM experiences e
        JOIN positions p ON e.position_id = p.position_id
        JOIN institutions i ON p.inst_id = i.inst_id
        ORDER BY e.start_date DESC
    """)
    skills = db.query("SELECT * FROM skills")
    return render_template('resume.html', experiences=experiences, skills=skills)

@sock.route('/ws/chat')
@login_required
def chat(ws):
    try:
        while True:
            data = ws.receive()
            print(f"Received message: {data}")  # Debug logging
            
            message_data = json.loads(data)
            timestamp = datetime.now().strftime('%H:%M:%S')
            name = current_user.email.split('@')[0]  # Use part of email as username
            formatted_message = f"[{name} {timestamp}]: {message_data['message']}"
            
            print(f"Sending message: {formatted_message}")  # Debug logging
            ws.send(json.dumps({"text": formatted_message}))

            timestamp = datetime.now().strftime('%H:%M:%S')
            ws.send(json.dumps({"text": f"[system {timestamp}]: <i>Message received</i>"}))
    except Exception as e:
        print(f"WebSocket error: {e}")  # Debug logging
        raise


@app.route("/users")
def users():
    """Display users as HTML"""
    if not db:
        return "<h1>Database not connected!</h1>"

    users = db.get_all_users()

    html = "<h1>Users in Database</h1>"
    html += "<table border='1' cellpadding='10'>"
    html += "<tr><th>ID</th><th>Name</th><th>Email</th></tr>"

    for user in users:
        html += f"""
        <tr>
            <td>{user['user_id']}</td>
            <td>{user['role']}</td>
            <td>{user['email']}</td>
        </tr>
        """

    html += "</table>"
    html += "<br><a href='/'>Back to home</a>"

    return html


@app.route("/users/json")
def users_json():
    """Display users as JSON"""
    if not db:
        return jsonify({"error": "Database not connected"})

    users = db.get_all_users()
    return jsonify({"users": users})


@app.route("/test")
def test():
    return '<img src="/static/images/gorilla.png">'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
