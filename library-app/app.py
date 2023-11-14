from sqlalchemy import or_, cast, String
from flask import Flask, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import csv
import psycopg2
import random
from webForms import BorrowerForm, PaymentForm, SearchForm


app = Flask(__name__)
# change the password to yours
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:[your password]@localhost:5432/library_db'
app.config['SECRET_KEY'] = 'team m'

db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/newborrower', methods=['GET', 'POST'])
def add_borrower():
    form = BorrowerForm()
    if form.validate_on_submit():
        borrower = Borrower(ssn=form.ssn.data, bname=form.bname.data, address=form.address.data, phone=form.phone.data)
        form.ssn.data = ''
        form.bname.data = ''
        form.address.data = ''
        form.phone.data = ''

        db.session.add(borrower)
        db.session.commit()
        flash("User registered successfully")
        
    return render_template("add_borrower.html", form = form)

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    form = SearchForm()
    searched = ""
    results = []
    if form.validate_on_submit():
        searched = form.searched.data
        query = (
            db.session.query(BookLoan, Book, Borrower)
            .join(Book, Book.isbn == BookLoan.isbn)
            .join(Borrower, Borrower.card_id == BookLoan.card_id)
            .filter(
                or_(
                    Book.isbn.ilike(f"%{searched}%"),
                    cast(Borrower.card_id, String).ilike(f"%{searched}%"),
                    Borrower.bname.ilike(f"%{searched}%")
                )
            )
        )

        results = query.all()
    return render_template("checkin.html", form=form, searched=searched, results=results)

@app.route('/checkin', methods=['GET', 'POST'])
def summary():
    return render_template("summary.html")

@app.route('/checkout')
def checkout():
    return render_template("checkout.html")

@app.route('/fines')
def fines():
    fines_unpaid = Fines.query.filter(Fines.paid == False).all()
    fines_paid = Fines.query.filter(Fines.paid == True).all()
    
    return render_template("fines.html", fines_unpaid=fines_unpaid, fines_paid=fines_paid)

@app.route('/payment/<int:id>')
def payment(id):
    fine = Fines.query.get_or_404(id)
    amount = None
    form = PaymentForm()
    if form.validate_on_submit():
        pass
    return render_template("payment.html", fine=fine, amount=amount, form=form)

@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        searched = form.searched.data
        query = (
            db.session.query(Book, Authors)
            .join(BookAuthors, Book.isbn == BookAuthors.isbn)
            .join(Authors, Authors.author_id == BookAuthors.author_id)
            .filter(
                or_(
                    Book.isbn.ilike(f"%{searched}%"),
                    Book.title.ilike(f"%{searched}%"),
                    Authors.name.ilike(f"%{searched}%")
                )
            )
        )

        results = query.all()
    return render_template("search.html", form=form, searched=searched, results=results)

# models
class Book(db.Model):
    __tablename__ = 'book'
    isbn = db.Column(db.String(13), primary_key=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)

class Authors(db.Model):
    __tablename__ = 'authors'
    author_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

class BookAuthors(db.Model):
    __tablename__ = 'book_authors'
    author_id = db.Column(db.Integer, nullable=False)
    isbn = db.Column(db.String(13), nullable=False, primary_key=True)
    db.ForeignKeyConstraint(['author_id'], ['authors.author_id'])
    db.ForeignKeyConstraint(['isbn'], ['book.isbn'])

class Borrower(db.Model):
    __tablename__ = 'borrower'
    card_id = db.Column(db.Integer, primary_key=True, nullable=False)
    ssn = db.Column(db.String(11), nullable=False, unique=True)
    bname = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(14), nullable=False)

class BookLoan(db.Model):
    __tablename__ = 'book_loans'
    loan_id = db.Column(db.Integer, primary_key=True, nullable=False)
    isbn = db.Column(db.String(13), nullable=False)
    card_id = db.Column(db.Integer, nullable=False)
    date_out = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    date_in = db.Column(db.Date)
    db.ForeignKeyConstraint(['isbn'], ['book.isbn'])
    db.ForeignKeyConstraint(['card_id'], ['borrower.card_id'])

class Fines(db.Model):
    __tablename__ = 'fines'
    loan_id = db.Column(db.Integer, primary_key=True, nullable=False)
    fine_amt = db.Column(db.Numeric(8, 2), nullable=False)
    paid = db.Column(db.Boolean, nullable=False)
    db.ForeignKeyConstraint(['loan_id'], ['book_loans.loan_id'])


def create_database():
    db_params = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'your password',
    }
    # Establish a connection to the default database
    connection = psycopg2.connect(**db_params)
    # Set isolation level to autocommit
    connection.set_isolation_level(0)
    cursor = connection.cursor()
    # Create a new database
    new_database_name = 'library_db'
    cursor.execute(f"CREATE DATABASE {new_database_name};")
    print(f"Database '{new_database_name}' created successfully.")
    connection.commit()
    connection.set_isolation_level(1)
    cursor.close()
    connection.close()

# read in books.csv
def read_tsv_data():
    # total No. of record: 25000
    # book w/ Author: 24972
    # book w/o Author: 28
    data = []
    with open('books.tsv', mode='r', newline='') as file:
        tsv_reader = csv.reader(file, delimiter='\t')
        next(tsv_reader, None)
        for line in tsv_reader:
            data.append(line)
    return data

# read in borrowers.csv
def read_csv_data():
    data = []
    with open('borrowers.csv', mode='r', newline='') as file:
        csv_reader = csv.reader(file)
        next(csv_reader, None)
        for line in csv_reader:
            data.append(line)
    return data

# populate the book, authors, and book_authors tables
def insert_records():
    try:
        # obtain the data from the files
        bookData = read_tsv_data()
        borrowerData = read_csv_data()

        count = 0
        for record in bookData:
            # populate the book table
            isbn13 = record[1]
            title = record[2]
            book = Book(isbn=isbn13, title=title)
            db.session.add(book)
            
            if record[3]:
                # populate the authors table
                author_name = record[3]
                author = Authors(name=author_name)
                db.session.add(author)

                # populate the book_authors table
                last_author = Authors.query.order_by(Authors.author_id.desc()).first()
                if last_author:
                    author_id = last_author.author_id
                    bookAuthor = BookAuthors(author_id=author_id, isbn=isbn13)
                    db.session.add(bookAuthor)
                    
            count += 1
            # print out the progress message
            if count % 1000 == 0:
                print(f"{count} / 25000 records inserted")

        # populate the borrower table
        for record in borrowerData:
            ssn = record[1]
            bname = record[2] + ' ' + record[3]
            address = record[5]
            phone = record[8]
            borrower = Borrower(ssn=ssn, bname=bname, address=address, phone=phone)
            db.session.add(borrower)
        
        db.session.commit()
        print("Book, Authors, and Book_Authors tables populated successfully")
    except Exception as e:
        print(f"An error occurred: {e}")

# generate sample data for book_loan and fines tables and populate them with the data
def generate_sample_fines():
    try:
        # query 10 instances of book and borrower data from the db
        book_records = Book.query.limit(10).all()
        borrower_records = Borrower.query.limit(10).all()
        
        for count in range(10):
            # populate the book_loan table
            date_out = datetime(2023, 1, count+1).date()
            due_date = date_out + timedelta(weeks=2)
            loan = BookLoan(isbn=book_records[count].isbn, card_id=borrower_records[count].card_id, date_out=date_out, due_date=due_date)
            db.session.add(loan)
            
            # populate the fines table
            last_loan = BookLoan.query.order_by(BookLoan.loan_id.desc()).first()
            if last_loan:
                loan_id = last_loan.loan_id
                paid = random.choice([True, False])
                fine_amt = round(random.uniform(1, 20), 2)
                bookAuthor = Fines(loan_id=loan_id, fine_amt=fine_amt, paid=paid)
                db.session.add(bookAuthor)
            
        db.session.commit()
        print("Sample data inserted into Book_Loans and Fines successfully")
    except Exception as e:
        print(f"An error occurred: {e}")


# comment out 'app.run(debug=True)' if you want to create a database
# comment out everything but 'app.run(debug=True)' if you want to run the app
if __name__ == '__main__':
    app.run(debug=True)
    # create_database()
    # with app.app_context():
    #     db.create_all()
    #     insert_records()
    #     generate_sample_fines()
