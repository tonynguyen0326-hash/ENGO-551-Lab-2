import os

from flask import Flask, session, redirect, request, render_template, url_for
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

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
@app.route("/books/<string:isbn>")
def book(isbn):
     # if user is not logged in, redirect to home page
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    # make sure book exists
    book = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()
    if book is None:
        return render_template("error.html", error="No results found.") 

    return render_template("book.html", book=book)