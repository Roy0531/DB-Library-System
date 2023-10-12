from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from database import init_db
from models import Book

app: Flask = Flask(__name__)
db: SQLAlchemy = init_db(app)


@app.route("/")
def test_page():
    # tack on a '1' to the first author's name to make sure updates work
    # also showing that raw SQL works
    db.session.execute(text("UPDATE AUTHORS SET Name = Name || :addToName "
                            "WHERE AUTHORS.Author_id=1"),
                       [{"addToName": "1"}])
    result: str = str(list(map(
        lambda book: book.title + " by " + str(list(map(
            lambda author: author.name, book.author))), # try the book.author field, make sure it queries that correctly
        db.session.execute(db.select(Book)).scalars()))) # try out a select query using the ORM
    db.session.commit()
    return render_template('test-page.html', result=result)


if __name__ == '__main__':
    app.run()
