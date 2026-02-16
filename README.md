# Project 2

ENGO 551

Continuing from Project 1, the book review website can now receive one review per person per book. The book page now also includes the reviews left by the user, the average rating, and number of ratings the book received from Google Books API, as well as a summarized description from Google Gemini API. Lastly, an API Access page is created for each book as well with the above descriptors as well as ISBN.

create.sql: creation of tables in SQL
import.py: how the books were imported from the books.csv file using SQL
application.py: @app.route functions for how the different urls work
test_gemini.py: page for testing gemini API key

within templates:
layout.html: basic layout for each .html page
index.html: layout for home page
register.html: layout for registration page
login.html: layout for login page
logout.html: layout for logout page
search.html: layout for search page
book.html: layout for each page of books
error.html: layout for if an invalid ISBN is put in the url for books