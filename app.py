from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h1>Velotra Creator Outreach</h1>
    <p>System is running successfully.</p>
    """


if __name__ == "__main__":
    app.run(debug=True)