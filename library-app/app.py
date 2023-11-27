from sqlalchemy import or_, cast, String, not_, text
from flask import Flask, render_template, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import re
from datetime import datetime, timedelta, date
import csv
import psycopg2
import random
from webForms import BorrowerForm, PaymentForm, SearchForm, BookForm, CheckOutForm
import sqlalchemy as db1
from datetime import date


app = Flask(__name__)
# change the password to yours
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Ryou053101Ori@localhost:5432/library_db'
app.config['SECRET_KEY'] = 'team m'

db = SQLAlchemy(app)
engine = db1.create_engine("postgresql://postgres:Ryou053101Ori@localhost:5432/library_db")

conn = engine.connect()

@app.route('/')
def index():
    return render_template("index.html")

# Handle registering new users
@app.route('/newborrower', methods=['GET', 'POST'])
def add_borrower():
    form = BorrowerForm()
    if form.validate_on_submit():
        ssn_pattern = re.compile(r'^\d{3}-\d{2}-\d{4}$')
        phone_pattern = re.compile(r'^\(\d{3}\) \d{3}-\d{4}$')
        phone=form.phone.data
        ssn=form.ssn.data
        # validate ssn and phone inputs
        if not ssn_pattern.match(ssn):
            flash("Invalid SSN Ipnut")
        elif not phone_pattern.match(phone):
            flash("Invalid Phone Ipnut")
        else:
            # check if the same ssn already exists in the database
            borrower = db.session.query(Borrower).filter(Borrower.ssn == ssn).first()
            if borrower:
                flash("This borrower already registered")
            else:
                borrower = Borrower(ssn=form.ssn.data, bname=form.bname.data, address=form.address.data, phone=form.phone.data)
                # clear the input form
                form.ssn.data = ''
                form.bname.data = ''
                form.address.data = ''
                form.phone.data = ''
                db.session.add(borrower)
                db.session.commit()
                flash("User Registered Successfully")
    return render_template("add_borrower.html", form = form)






@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    searched = ""
    if form.validate_on_submit():
        searched = form.searched.data
        return redirect(url_for('results', searched=searched))
    return render_template("search.html", form=form)

@app.route('/results/<searched>', methods=['GET', 'POST'])
def results(searched):
    form = BookForm()
    base_query = (
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

    query_aval = base_query.filter(
            not_(
                db.session.query(BookLoan.isbn)
                .filter(BookLoan.isbn == Book.isbn)
                .exists()
            )
        ).distinct().all()
    
    query_unaval = base_query.join(BookLoan, BookLoan.isbn == Book.isbn).distinct().all()
    
    form.books.choices = [(f"{book.isbn}_{book.title}_{author.name}", "") for book, author in query_aval]
    if form.validate_on_submit():
        session['selected_books'] = form.books.data
        return redirect(url_for('checkout'))
    else:
        print("Validation Failed")
    return render_template("results.html", searched=searched, form=form, query_unaval=query_unaval)

@app.route('/checkout', methods=['Get','POST'])
def checkout():
    selected_books = session.get('selected_books', [])
    book_data_list = []
    for book in selected_books:
        isbn, title, names = book.split('_')
        book_data = {
            'isbn': isbn,
            'title': title,
            'author': names
        }
        book_data_list.append(book_data)
        
    checkout_count = len(book_data_list)
    form = CheckOutForm()
    loan_count = 0
    over_limit = False
    due_date = None
    if form.validate_on_submit():
        card_id = form.card_id.data
        loan_count = db.session.query(BookLoan).filter(BookLoan.card_id ==card_id).count()
        if checkout_count + loan_count <= 3:
            for book in book_data_list:
                date_out = date.today()
                due_date = date_out + timedelta(weeks=2)
                loan = BookLoan(isbn=book['isbn'], card_id=card_id, date_out=date_out, due_date=due_date)
                db.session.add(loan)
                query = text("""
                SELECT loan_id
                FROM book_loans
                WHERE isbn = :isbn AND card_id = :card_id
                """)
                loan_id = conn.execute(query, {'isbn':book['isbn'], 'card_id':card_id}).fetchone()
                query = text("""
                INSERT INTO book_loans(loan_id, fine_amt)
                VALUES (:loan_id, 0.00)
                """)
                conn.execute(query, {'loan_id': loan_id[0]})
            db.session.commit()
            conn.commit()

        else:
            over_limit = True
        return render_template('summary_out.html', over_limit=over_limit, book_data_list=book_data_list, due_date=due_date, checkout_count=checkout_count, loan_count=loan_count)
    return render_template("checkout.html", form=form, over_limit=over_limit, book_data_list=book_data_list)









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
            ).distinct()
        )
        
        results = query.all()
    return render_template("checkin.html", form=form, searched=searched, results=results)

@app.route('/summary_in/<id>')
def summary_in(id):
    # this id is loan_id
    loan_to_update = db.session.query(BookLoan).filter(BookLoan.loan_id == id).first()
    if loan_to_update:
        current_date = date.today()
        loan_to_update.date_in = current_date
        db.session.commit()
        overdue=False
        date_difference = loan_to_update.date_in - loan_to_update.date_out
        if date_difference > timedelta(days=14):
            overdue=True
        remaining_loans = db.session.query(BookLoan).filter(BookLoan.card_id == loan_to_update.card_id).filter(BookLoan.loan_id != loan_to_update.loan_id).all()
    return render_template("summary_in.html", loan_to_update=loan_to_update, remaining_loans=remaining_loans, overdue=overdue)

@app.route('/fines')
def fines():
    fines_unpaid = db.session.query(Fines).filter(Fines.paid == False).all()
    fines_paid = db.session.query(Fines).filter(Fines.paid == True).all()
    return render_template("fines.html", fines_unpaid=fines_unpaid, fines_paid=fines_paid)

@app.route('/payment/<id>', methods=['GET', 'POST'])
def payment(id):
    fine = Fines.query.get_or_404(id)
    entered_amount = 0.0
    form = PaymentForm()
    if form.validate_on_submit():
        entered_amount = form.amount.data
        if entered_amount != float(fine.fine_amt):
            flash('Amount does not match the fine amount.', 'error')
        else:
            fine.paid = True
            db.session.commit()
            session['loan_id'] = fine.loan_id
            return redirect(url_for('receipt'))
    return render_template("payment.html", fine=fine, form=form)

@app.route('/receipt', methods=['GET'])
def receipt():
    loan_id = session.get('loan_id', [])
    
    return render_template("receipt.html", loan_id=loan_id)


# will go through fines database and will update all the fines that haven't been paid
def update_day_fines():
    query = text("""
    UPDATE FINES 
    SET fine_amt = 
    CASE 
        WHEN (fines.paid = FALSE OR fines.paid is NULL) AND BOOK_LOANS.due_date < CURRENT_DATE AND BOOK_LOANS.date_in is NULL
        THEN EXTRACT(EPOCH FROM AGE(CURRENT_DATE, BOOK_LOANS.due_date))/(24*3600)*0.25
        ELSE fine_amt
    END
	FROM BOOK_LOANS
	WHERE fines.loan_id = book_loans.loan_id;
""")
    conn.execute(query)
    conn.commit()
    # query = fines.select()
    # result = conn.execute(query).fetchall()




# Models
class Book(db.Model):
    __tablename__ = 'book'
    isbn = db.Column(db.String(10), primary_key=True, nullable=False)
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
    paid = db.Column(db.Boolean, nullable=True)
    db.ForeignKeyConstraint(['loan_id'], ['book_loans.loan_id'])

# Create a database named 'library_db'
def create_database():
    db_params = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Ryou053101Ori',
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
    # Close the connection
    connection.close()

# Read in data from books.csv and return an array of the books' data
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

# Read in data from borrowers.csv and retun an array of the borrowers' data
def read_csv_data():
    data = []
    with open('borrowers.csv', mode='r', newline='') as file:
        csv_reader = csv.reader(file)
        next(csv_reader, None)
        for line in csv_reader:
            data.append(line)
    return data

# Populate the book, authors, and book_authors tables
def insert_records():
    try:
        # read in data from the files
        bookData = read_tsv_data()
        borrowerData = read_csv_data()
        # count the number of records inserted
        count = 0
        # each record is an array: [isbn10, isbn13, title, author, cover, publisher, pages]
        for record in bookData:
            # populate the book table
            isbn10 = record[0]
            title = record[2]
            book = Book(isbn=isbn10, title=title)
            db.session.add(book)
            # populate the authors table
            # books w/o aithors doesn't have record[3]
            if record[3]:
                author_name = record[3]
                author = Authors(name=author_name)
                db.session.add(author)
                # populate the book_authors table
                # query the author data that has just been inserted in the above lines
                last_author = Authors.query.order_by(Authors.author_id.desc()).first()
                if last_author:
                    author_id = last_author.author_id
                    bookAuthor = BookAuthors(author_id=author_id, isbn=isbn10)
                    db.session.add(bookAuthor)
            count += 1
            # print out the progress message
            if count % 1000 == 0:
                print(f"{count} / 25000 records inserted")

        # populate the borrower table
        # each record is an array: [id, ssn, first_name, last_name, email, address, city, state, phone]
        for record in borrowerData:
            ssn = record[1]
            bname = record[2] + ' ' + record[3]
            address = record[5]
            phone = record[8]
            borrower = Borrower(ssn=ssn, bname=bname, address=address, phone=phone)
            db.session.add(borrower)
        # commit the changes to the database
        db.session.commit()
        print("Book, Authors, and Book_Authors tables populated successfully")
    except Exception as e:
        print(f"An error occurred: {e}")

# Generate sample data for book_loan and fines tables and populate them with the sample data
def generate_sample_fines():
    try:
        # query the first 10 instances of book and borrower data from the database
        book_records = db.session.query(Book).limit(10).all()
        borrower_records = db.session.query(Borrower).limit(10).all()
        
        for count in range(10):
            # populate the book_loan table
            # generate a sample date value
            date_out = datetime(2023, 1, count+1).date()
            # set the due data to date_out + 14 days 
            due_date = date_out + timedelta(weeks=2)
            loan = BookLoan(isbn=book_records[count].isbn, card_id=borrower_records[count].card_id, date_out=date_out, due_date=due_date)
            db.session.add(loan)
            
            # populate the fines table
            # query the book loan data that has just been inserted in the above lines
            last_loan = db.session.query(BookLoan).order_by(BookLoan.loan_id.desc()).first()
            if last_loan:
                loan_id = last_loan.loan_id
                # randomly decide if this loan is paid or not
                paid = random.choice([True, False])
                # generate a random fine amount with 2 decimal places
                fine_amt = round(random.uniform(1, 20), 2)
                bookAuthor = Fines(loan_id=loan_id, fine_amt=fine_amt, paid=paid)
                db.session.add(bookAuthor)
        # commit the changes to the database 
        db.session.commit()
        print("Sample data inserted into Book_Loans and Fines successfully")
    except Exception as e:
        print(f"An error occurred: {e}")


# comment out 'app.run(debug=True)' to create a database
# comment out everything but 'app.run(debug=True)' to run the app
if __name__ == '__main__':
    app.run(debug=True)
    # create_database()
    # with app.app_context():
    #     db.create_all()
    #     insert_records()
    #     generate_sample_fines()
