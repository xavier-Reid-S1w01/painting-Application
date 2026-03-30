from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    #Home page
    return "Title"

if __name__ == "__main__":
    app.run(debug=True)