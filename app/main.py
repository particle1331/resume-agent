from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>Hello, world!</h1>
    <p>Flask is working with <code>uv</code>! 🚀</p>
    <p>Go to <a href="/test">/test</a> to see another page</p>
    """

@app.route("/test")
def test():
    return '<img src="/static/gorilla.jpeg">'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
