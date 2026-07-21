from flask import Flask, render_template, request, g
import sqlite3 

app = Flask(__name__)

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        # Allows accessing columns by name in templates (e.g., row['MovementName'])
        db.row_factory = sqlite3.Row
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


# HOME ROUTE
@app.route("/")
def home():
    all_paintings = query_db("SELECT * FROM Paintings")
    return render_template("home.html", Paintings=all_paintings)

@app.route('/artist')
def artist():
    # Fetch artists AND the first painting's ImageURL for each artist
    all_artists = query_db('''
        SELECT Artist.ArtistID,
               Artist.ArtistName,
               Paintings.ImageURL AS ArtistImage
        FROM Artist
        LEFT JOIN Paintings ON Artist.ArtistID = Paintings.ArtistID
        GROUP BY Artist.ArtistID
    ''')

    # Filter paintings if an artist link was clicked
    selected_artist_id = request.args.get('artist_id')

    if selected_artist_id:
        paintings = query_db("SELECT * FROM Paintings WHERE ArtistID = ?", [selected_artist_id])
    else:
        paintings = query_db("SELECT * FROM Paintings")

    return render_template("artist.html", artists=all_artists, Paintings=paintings)


@app.route('/artworks')
def artworks():
    # Fetch movements AND the first painting's ImageURL for each movement
    all_movements = query_db('''
        SELECT ArtMovement.MovementID, 
               ArtMovement.MovementName, 
               Paintings.ImageURL AS MovementImage
        FROM ArtMovement
        LEFT JOIN Paintings ON ArtMovement.MovementID = Paintings.MovementID
        GROUP BY ArtMovement.MovementID
    ''')
    
    # Filter paintings if a movement link was clicked
    selected_movement_id = request.args.get('movement_id')
    
    if selected_movement_id:
        paintings = query_db("SELECT * FROM Paintings WHERE MovementID = ?", [selected_movement_id])
    else:
        paintings = query_db("SELECT * FROM Paintings")

    return render_template("artworks.html", movements=all_movements, Paintings=paintings)


if __name__ == "__main__":
    app.run(debug=True)