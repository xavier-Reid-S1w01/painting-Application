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
    # Fetch artists AND the first painting's ImageURL as cover image
    all_artists = query_db('''
        SELECT Artist.ArtistID,
               Artist.ArtistName,
               Paintings.ImageURL AS ArtistImage
        FROM Artist
        LEFT JOIN Paintings ON Artist.ArtistID = Paintings.ArtistID
        GROUP BY Artist.ArtistID
    ''')

    return render_template("artist.html", artists=all_artists)


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

@app.route('/filter')
def filter_page():
    # Read the parameter from the URL bar
    selected_movement_id = request.args.get('movement_id')
    selected_artist_id = request.args.get('artist_id')

    #  Query the database depending on what was clicked
    if selected_movement_id:
        # Fetch paintings for the clicked movement
        paintings = query_db("SELECT * FROM Paintings WHERE MovementID = ?", [selected_movement_id])
        # Fetch the movement details for a page title heading
        category_title = query_db("SELECT MovementName FROM ArtMovement WHERE MovementID = ?", [selected_movement_id], one=True)
        title = category_title['MovementName'] if category_title else "Filter Results"

    elif selected_artist_id:
        # Fetch paintings by the clicked artist
        paintings = query_db("SELECT * FROM Paintings WHERE ArtistID = ?", [selected_artist_id])
        # Fetch the artist details for a page title heading
        category_title = query_db("SELECT ArtistName FROM Artist WHERE ArtistID = ?", [selected_artist_id], one=True)
        title = category_title['ArtistName'] if category_title else "Filter Results"

    else:
        # Fallback: if no query parameter is passed
        paintings = query_db("SELECT * FROM Paintings")
        title = "All Paintings"

    # Pass the filtered results and title into filter.html
    return render_template("filter.html", Paintings=paintings, page_title=title)

@app.route('/painting/<int:painting_id>')
def painting_detail(painting_id):
    painting = query_db("SELECT * FROM Paintings WHERE PaintingID = ?", [painting_id], one=True)
    return render_template("painting_detail.html", painting=painting)


if __name__ == "__main__":
    app.run(debug=True)