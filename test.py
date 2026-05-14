from flask import Flask, render_template,g
import sqlite3 

app = Flask(__name__)

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.route("/")
def home():
    # This grabs all rows from the Paintings table
    all_paintings = query_db("SELECT * FROM Paintings")
    # This sends that list to the HTML
    return render_template("home.html", Paintings=all_paintings)




if __name__ == "__main__":
    app.run(debug=True)