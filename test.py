
# Import Flask framework tools for building the web app
from flask import Flask, render_template, request, g
# Import SQLite module to interact with the database
import sqlite3 

# Initialize the Flask application instance
app = Flask(__name__)

# Filepath to the SQLite database file
DATABASE = 'database.db'


def get_db():
    """
    Opens a new database connection if one doesn't exist for the current context.
    'g' is a special Flask object that stores data unique to a single request.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        
        # Configure rows to act like dictionaries so columns can be accessed by name
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """
    Automatically closes the database connection when the request finishes
    or the app context shuts down.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """
    Helper function to run SQL queries easily.
    - query: SQL statement to execute.
    - args: Parameters to safely plug into the query (prevents SQL injection).
    - one: If True, returns only the first result instead of a list.
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    
    # Return a single record if requested, otherwise return the full list of records
    return (rv[0] if rv else None) if one else rv


# HOME PAGE
@app.route("/")
def home():
    """Fetches all paintings from the database and renders the homepage."""
    all_paintings = query_db("SELECT * FROM Paintings")
    return render_template("home.html", Paintings=all_paintings)


# ARTISTS DIRECTORY PAGE
@app.route('/artist')
def artist():
    """
    Fetches all artists alongside the cover image of their first available painting,
    then renders the artist directory page.
    """
    all_artists = query_db('''
        SELECT Artist.ArtistID,
               Artist.ArtistName,
               Paintings.ImageURL AS ArtistImage
        FROM Artist
        LEFT JOIN Paintings ON Artist.ArtistID = Paintings.ArtistID
        GROUP BY Artist.ArtistID
    ''')

    return render_template("artist.html", artists=all_artists)


# ARTWORKS PAGE (WITH OPTIONAL FILTERING)
@app.route('/artworks')
def artworks():
    """
    Fetches movement categories with sample cover images.
    Filters paintings by movement if 'movement_id' is passed in URL query parameters.
    """
    # Query distinct movements and attach a representative image from the Paintings table
    all_movements = query_db('''
        SELECT ArtMovement.MovementID, 
               ArtMovement.MovementName, 
               Paintings.ImageURL AS MovementImage
        FROM ArtMovement
        LEFT JOIN Paintings ON ArtMovement.MovementID = Paintings.MovementID
        GROUP BY ArtMovement.MovementID
    ''')
    
    # Check URL query parameters (e.g., /artworks?movement_id=2)
    selected_movement_id = request.args.get('movement_id')
    
    # Conditionally load filtered or unfiltered paintings
    if selected_movement_id:
        paintings = query_db("SELECT * FROM Paintings WHERE MovementID = ?", [selected_movement_id])
    else:
        paintings = query_db("SELECT * FROM Paintings")

    return render_template("artworks.html", movements=all_movements, Paintings=paintings)


# DYNAMIC FILTER RESULTS PAGE
@app.route('/filter')
def filter_page():
    """
    Handles filtering logic for specific artists or movements.
    Dynamically sets the page title based on the selected filter.
    """
    # Extract query parameters from URL (e.g., /filter?artist_id=3)
    selected_movement_id = request.args.get('movement_id')
    selected_artist_id = request.args.get('artist_id')

    if selected_movement_id:
        # Fetch paintings belonging to the selected art movement
        paintings = query_db("SELECT * FROM Paintings WHERE MovementID = ?", [selected_movement_id])
        
        # Get category name for the header title
        category_title = query_db("SELECT MovementName FROM ArtMovement WHERE MovementID = ?", [selected_movement_id], one=True)
        title = category_title['MovementName'] if category_title else "Filter Results"

    elif selected_artist_id:
        # Fetch paintings created by the selected artist
        paintings = query_db("SELECT * FROM Paintings WHERE ArtistID = ?", [selected_artist_id])
        
        # Get artist name for the header title
        category_title = query_db("SELECT ArtistName FROM Artist WHERE ArtistID = ?", [selected_artist_id], one=True)
        title = category_title['ArtistName'] if category_title else "Filter Results"

    else:
        # Fallback view: Display all paintings if no parameter was provided
        paintings = query_db("SELECT * FROM Paintings")
        title = "All Paintings"

    return render_template("filter.html", Paintings=paintings, page_title=title)


# SINGLE PAINTING DETAILS PAGE
@app.route('/painting/<int:painting_id>')
def painting_detail(painting_id):
    """
    Fetches comprehensive details for a specific painting by joining
    the Paintings table with Artist and ArtMovement tables using its ID.
    """
    painting = query_db('''
        SELECT Paintings.*, 
               Artist.ArtistName, 
               ArtMovement.MovementName
        FROM Paintings
        LEFT JOIN Artist ON Paintings.ArtistID = Artist.ArtistID
        LEFT JOIN ArtMovement ON Paintings.MovementID = ArtMovement.MovementID
        WHERE Paintings.PaintingsID = ?
    ''', [painting_id], one=True)

    return render_template("painting_detail.html", painting=painting)


# SEARCH RESULTS PAGE
@app.route('/search')
def search():
    """
    Searches the database for paintings where the title OR artist name 
    matches the user's search query string.
    """
    # Retrieve user query parameter and strip whitespace
    search_query = request.args.get('query', '').strip()
    
    if search_query:
        # SQL LIKE search using wildcard operators (%)
        paintings = query_db('''
            SELECT Paintings.*, Artist.ArtistName 
            FROM Paintings
            LEFT JOIN Artist ON Paintings.ArtistID = Artist.ArtistID
            WHERE Paintings.Title LIKE ? OR Artist.ArtistName LIKE ?
        ''', [f'%{search_query}%', f'%{search_query}%'])
    else:
        paintings = []

    # Reuses the generic filter.html template to render search results
    return render_template(
        "filter.html", 
        Paintings=paintings, 
        page_title=f"Search Results for '{search_query}'"
    )

if __name__ == "__main__":
    # Start the Flask local development server with debug logging enabled
    app.run(debug=True)