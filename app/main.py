import time
from flask import Flask, jsonify
from app.database import wait_for_db

db = wait_for_db()
app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h1>Flask + PostgreSQL 🚀</h1>
    <p>Flask is now connected to a database!</p>
    <ul>
        <li><a href="/users">View all users</a></li>
        <li><a href="/users/json">View users as JSON</a></li>
        <li><a href="/test">Test page</a></li>
    </ul>
    """


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
    return '<img src="/static/gorilla.png">'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
