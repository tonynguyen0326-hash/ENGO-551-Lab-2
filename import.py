import os
import csv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    # read in .csv file
    f = open("books.csv")
    reader = csv.reader(f)
    # skip header row
    next(reader)
    # loop through .csv file
    for isbn, title, author, year in reader:
        db.execute(
            text("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"), {"isbn": isbn, "title":title, "author": author, "year": year}
        )
    db.commit()

if __name__ == "__main__":
    main()