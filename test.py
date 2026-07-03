from flask import Flask, render_template, g
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


# HOME ROUTE Combines your database query with your home page
@app.route("/")
def home():
    # This grabs all rows from the Paintings table
    all_paintings = query_db("SELECT * FROM Paintings")
    # This sends that list to the HTML
    return render_template("home.html", Paintings=all_paintings)

@app.route('/artworks')
def artworks():
    # 1. Look for a text name in the URL instead of an ID (e.g., ?movement=Impressionism)
    selected_movement = request.args.get('movement', type=str)
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 2. Fetch the movement names to build your sliding menu
    cursor.execute("SELECT MovementName FROM ArtMovement")
    # Extract just the strings from the database tuples
    movements_data = [row[0] for row in cursor.fetchall()]
    
    # 3. Filter paintings by text name
    if selected_movement:
        # Change 'Movement' to match your exact column name in the Paintings table (e.g., Genre)
        cursor.execute("SELECT * FROM Paintings WHERE Movement = ?", (selected_movement,))
    else:
        cursor.execute("SELECT * FROM Paintings")
        
    paintings_data = cursor.fetchall()
    conn.close()
    
    return render_template('artworks.html', 
                           Movements=movements_data, 
                           Paintings=paintings_data, 
                           selected_movement=selected_movement)



if __name__ == "__main__":
    app.run(debug=True)