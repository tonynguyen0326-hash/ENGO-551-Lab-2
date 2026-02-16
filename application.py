import os
import requests

from flask import Flask, session, redirect, request, render_template, url_for, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# main page
@app.route("/")
def index():
    return render_template("index.html")

# registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # get data from registration form
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        # check if passwords match, show error message if they don't
        if password != confirm:
            return render_template("register.html", error="Passwords do not match.")

        # check to see if username is already taken
        taken = db.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()

        # show error message if username is already taken
        if taken:
            return render_template("register.html", error="Username already taken.")
        
         # hash password for security
        hashed = generate_password_hash(password)

        # insert username and hashed password into table of users
        db.execute(
            text("INSERT INTO users (username, password) VALUES (:username, :password)"),
            {"username": username, "password": hashed}
        )

        db.commit()

        # log in new user
        user = db.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()

        # if registration fails
        if user is None:
            return render_template("register.html", error="Registration failed. Please try again.")

        session["user_id"] = user.id
        session["username"] = user.username

        return redirect(url_for("search"))
    else:
        return render_template("register.html")
    
# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # get login data
        username = request.form.get("username")
        password = request.form.get("password")   
    
        # check user credentials
        user = db.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()

        if not user:
            return render_template("login.html", error="Username not found.")
        
        if not check_password_hash(user.password, password):
            return render_template("login.html", error="Incorrect Password.")
    
        # store user credentials in session
        session["user_id"] = user.id
        session["username"] = user.username

        # redirect to search page
        return redirect(url_for("search"))

    return render_template("login.html")

# logout page
@app.route("/logout")
def logout():
    # if user is not logged in, redirect to home page
    if "user_id" not in session:
        return redirect(url_for("index"))
    # remove session data
    session.clear()
    return render_template("logout.html")

# search page for books
@app.route("/search", methods=["GET", "POST"])
def search():
     # if user is not logged in, redirect to home page
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    # initialize books variable
    books = None

    if request.method == "POST":
        # get info from book table
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        author = request.form.get("author")
        year = request.form.get("year")

        # query search results
        query = text(
            "SELECT * FROM books WHERE (:isbn IS NULL OR isbn ILIKE '%' || :isbn || '%') AND (:title IS NULL OR title ILIKE '%' || :title || '%') AND (:author IS NULL OR author ILIKE '%' || :author || '%') AND (:year IS NULL OR year = :year)")

        books = db.execute(
            query, {"isbn": isbn or None, "title": title or None, "author": author or None, "year": year or None}).fetchall()

    return render_template("search.html", books=books)

# page for each book
@app.route("/books/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    
    # if user is not logged in, redirect to home page
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    # make sure book exists
    book = db.execute(
        text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}
        ).fetchone()

        # initalize error
    error = None
    
    if book is None:
        return render_template("error.html", error="No results found.") 
    
    # get info from Google Books 
    google = google_books(isbn)
    
    if google and google.get("description"):
        summary = summarize(google.get("description"))
        avg = google.get("averageRating")
        count = google.get("ratingsCount")
    else:
        summary = "No summary available."

    
    if request.method == "POST":

        # get rating and review
        rating = request.form.get("rating")
        review = request.form.get("review")

        # make sure rating and review are not empty
        if not rating or not review:
            error="All fields required for review."

        # make sure user has not reviewed book already
        exist = db.execute(
            text("SELECT * FROM reviews WHERE user_id = :user_id AND isbn = :isbn"), {"user_id": session["user_id"], "isbn": isbn}
        ).fetchone()

        if exist:
            return render_template("book.html", book=book, error="Only one review per book.")    

        # insert new review
        db.execute(text("INSERT INTO reviews (user_id, isbn, rating, review) VALUES (:user_id, :isbn, :rating, :review)"),
                   {"user_id": session["user_id"], "isbn": isbn, "rating": int(rating), "review": review}
        )

        db.commit()

        # get reviews
    reviews = db.execute(
        text("SELECT review.rating, review.review, review.time_of, u.username FROM reviews review JOIN users u ON review.user_id = u.id WHERE review.isbn = :isbn ORDER BY review.time_of DESC"), {"isbn": isbn}
    ).fetchall()

    return render_template("book.html", book=book, reviews=reviews, error=error, google=google, summary=summary, avg=avg, count=count)

# for Google Books data
def google_books(isbn):
    
    # get response
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{isbn}"})
    
    # check status code
    if res.status_code != 200:
        return
    
    # turn JSON to python
    data = res.json()

    # if nothing found in Google Books
    if "items" not in data:
        return None
    
    # access data
    volumeInfo = data["items"][0]["volumeInfo"]
    averageRating = volumeInfo.get("averageRating")
    ratingsCount = volumeInfo.get("ratingsCount")
    description = volumeInfo.get("description")
    publishedDate = volumeInfo.get("publishedDate")
    
    # initialize both ISBN types
    isbn10 = None
    isbn13 = None

    # find identifiers
    industryIdentifiers = volumeInfo.get("industryIdentifiers")

    if industryIdentifiers:
        for id in industryIdentifiers:
            if id.get("type") == "ISBN_10":
                isbn10 = id.get("identifier")
            elif id.get("type") == "ISBN_13":
                isbn13 = id.get("identifier")

    return {
        "averageRating": averageRating,
        "ratingsCount": ratingsCount,
        "description": description,
        "publishedDate": publishedDate,
        "ISBN_10": isbn10,
        "ISBN_13": isbn13
    }

# API Key and AI client
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

def summarize(description):
    
    # make sure description exists
    if not description:
        return None
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Summarize this text using less than 50 words: {description}"
    )
    
    return response.text

@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):

    # make sure book exists
    book = db.execute(
        text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}
        ).fetchone()   
    
    # return 404 error if book not found
    if book is None:
        return abort(404, description="Book not in database. Please try again.")
    
    # get Google Books info
    google = google_books(isbn)

    # JSON response
    data = {
        "title": book.title,
        "author": book.author,
        "publishedDate": google.get("publishedDate"),
        "ISBN_10": google.get("ISBN_10"),
        "ISBN_13": google.get("ISBN_13"),
        "reviewCount": google.get("ratingsCount"),
        "averageRating": google.get("averageRating"),
        "description": google.get("description"),
        "summarizedDescription": summarize(google.get("description"))
    }
    
    return jsonify(data)