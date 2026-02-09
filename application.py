import os

from flask import Flask, session, redirect, request, render_template, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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

        # check if passwords match
        if password != confirm:
            return "Passwords do not match."
        
        print(f"Username: {username}, Password: {password}")

        return redirect(url_for("index"))
    else:
        return render_template("register.html")
    