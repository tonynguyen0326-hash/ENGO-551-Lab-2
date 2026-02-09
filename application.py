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


@app.route("/")
def index():
    return redirect("/register")

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

        return redirect(url_for("index"))
    else:
        return render_template("register.html")
    