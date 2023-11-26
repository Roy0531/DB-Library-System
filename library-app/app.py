from sqlalchemy import or_, cast, String, not_
from flask import Flask, render_template, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import re
from datetime import datetime, timedelta, date
import csv
import psycopg2
import random
from webForms import BorrowerForm, PaymentForm, SearchForm, BookForm, CheckOutForm

load_dotenv()
db_pass = os.environ.get('DATABASE_PASSWORD')

app = Flask(__name__)
# change the password to yours
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{db_pass}@localhost:5432/library_db'
app.config['SECRET_KEY'] = 'team m'

db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template("index.html")

# Handle registering new users
@app.route('/newborrower', methods=['GET', 'POST'])
def add_borrower():
    # create a form object that takes care of user info submission
    form = BorrowerForm()
    # validate if the form is at least filled in with some user input
    if form.validate_on_submit():
        # regular expression for validating ssn input
        ssn_pattern = re.compile(r'^\d{3}-\d{2}-\d{4}$')
        # regular expression for validating phone number input
        phone_pattern = re.compile(r'^\(\d{3}\) \d{3}-\d{4}$')
        # get the ssn and phone number input
        phone=form.phone.data
        ssn=form.ssn.data
        # validate ssn and phone inputs
        if not ssn_pattern.match(ssn):
            # indicate the user that the ssn input is invalid
            flash("Invalid SSN Ipnut")
        elif not phone_pattern.match(phone):
            # indicate the user that the ssn input is invalid
            flash("Invalid Phone Ipnut")
        else:
            # check if the same ssn already exists in the database
            borrower = db.session.query(Borrower).filter(Borrower.ssn == ssn).first()
            if borrower:
                # indicate the user that the ssn already exists in the database
                flash("This borrower already registered")
            else:
                # if all the inputs are valid, create a new borrower instance
                borrower = Borrower(ssn=form.ssn.data, bname=form.bname.data, address=form.address.data, phone=form.phone.data)
                # clear the input form
                form.ssn.data = ''
                form.bname.data = ''
                form.address.data = ''
                form.phone.data = ''
                # add the borrower instance to the database
                db.session.add(borrower)
                # commit the change to the database
                db.session.commit()
                # indicate the user that the new borrower successfully registered
                flash("User Registered Successfully")
    # display the add_borrower page
    return render_template("add_borrower.html", form = form)

# Handle searching for books
@app.route('/search', methods=['GET', 'POST'])
def search():
    # create a form object that takes are of search terms submission
    form = SearchForm()
    searched = ""
    # validate if the form is at least filled in with some saerch terms
    if form.validate_on_submit():
        # get the search terms this user typed in
        searched = form.searched.data
        # redirect user to results page
        return redirect(url_for('results', searched=searched))
    # display the search page
    return render_template("search.html", form=form)

# Handle displaying search results
@app.route('/results/<searched>', methods=['GET', 'POST'])
def results(searched):
    # create a form object that takes care of books' data submittion
    form = BookForm()
    # base query used to query for books currently avairable and unavairable
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
    # query for books currently available
    query_aval = base_query.filter(
            not_(
                db.session.query(BookLoan.isbn)
                .filter(BookLoan.isbn == Book.isbn)
                .exists()
            )
        ).distinct().all()
    # query for books currently unavailable
    query_unaval = base_query.join(BookLoan, BookLoan.isbn == Book.isbn).distinct().all()
    
    form.books.choices = [(f"{book.isbn}_{book.title}_{author.name}", "") for book, author in query_aval]

    if form.validate_on_submit():
        # pass the selected books data to checkout() function below
        session['selected_books'] = form.books.data
        return redirect(url_for('checkout'))
    else:
        print("Validation Failed")
    # display the results page
    return render_template("results.html", searched=searched, form=form, query_unaval=query_unaval)

# Handle checking out books
@app.route('/checkout', methods=['Get','POST'])
def checkout():
    # get the selected books data passed from results() function above
    selected_books = session.get('selected_books', [])
    book_data_list = []
    # create a list of dictionary of books to chekcout 
    for book in selected_books:
        isbn, title, names = book.split('_')
        book_data = {
            'isbn': isbn,
            'title': title,
            'author': names
        }
        book_data_list.append(book_data)
    # get the number of books this user is borrowing
    checkout_count = len(book_data_list)
    # create a form object that takes care of card id submittion
    form = CheckOutForm()
    # used in the input validation below
    loan_count = 0
    over_limit = False
    due_date = None
    # validate card id input
    if form.validate_on_submit():
        # get the card id value this user typed in
        card_id = form.card_id.data
        # get the number of book loan this user already has
        loan_count = db.session.query(BookLoan).filter(BookLoan.card_id ==card_id).count()
        # check if the total number of book loan for this user does not exceed 3
        if checkout_count + loan_count <= 3:
            # create book loan instances for each book this user is borrowing
            for book in book_data_list:
                # get the date of today
                date_out = date.today()
                # set the due date to 2 weeks after today's date
                due_date = date_out + timedelta(weeks=2)
                loan = BookLoan(isbn=book['isbn'], card_id=card_id, date_out=date_out, due_date=due_date)
                # add this new loan instance to the database
                db.session.add(loan)
            # commit the changes to the database
            db.session.commit()
        else:
            # the total number of loan this user is going to have exceed 3
            over_limit = True
        # display the summary page
        return render_template('summary_out.html', over_limit=over_limit, book_data_list=book_data_list, due_date=due_date, checkout_count=checkout_count, loan_count=loan_count)
    # display the ckeck out page
    return render_template("checkout.html", form=form, over_limit=over_limit, book_data_list=book_data_list)

# Handle chcking in books
@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    # create a form object that takes are of search terms submission 
    form = SearchForm()
    searched = ""
    results = []
    # validate if the form is at least filled in with some saerch terms
    if form.validate_on_submit():
        # get the search terms this user typed in
        searched = form.searched.data
        # create a query object that fetch loan data based on the searhc term gievn
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
        # query the data
        results = query.all()
    # display the checkin page
    return render_template("checkin.html", form=form, searched=searched, results=results)

# Handle displaying 
@app.route('/summary_in/<id>')
def summary_in(id):
    # this id is loan_id of the books that are going to be checked in
    # query for the book to be checked in
    loan_to_update = db.session.query(BookLoan).filter(BookLoan.loan_id == id).first()
    if loan_to_update:
        # get the date of today
        current_date = date.today()
        loan_to_update.date_in = current_date
        db.session.commit()
        overdue=False
        date_difference = loan_to_update.date_in - loan_to_update.date_out
        if date_difference > timedelta(days=14):
            overdue=True
        # query for the remaining loans of this user
        remaining_loans = db.session.query(BookLoan).filter(BookLoan.card_id == loan_to_update.card_id).filter(BookLoan.loan_id != loan_to_update.loan_id).all()
    # display the summary page
    return render_template("summary_in.html", loan_to_update=loan_to_update, remaining_loans=remaining_loans, overdue=overdue)

# Handle displaying the fines
@app.route('/fines')
def fines():
    # query for book loans that have been returned and  that their date_in is later than the due_date
    returned_overdue_loans = db.session.query(BookLoan).filter(
        BookLoan.date_in is not None, BookLoan.due_date < BookLoan.date_in
    ).all()
    # Update fines for overdue books that have been returned
    for loan in returned_overdue_loans:
        # Calculate the number of days overdue
        days_overdue = (loan.date_in - loan.due_date).days
        # Calculate the fine amount based on the rate of $0.25/day
        fine_amount = days_overdue * 0.25
        # Update the fine_amt of the unpaid fines for the corresponding loan_id
        fines_entry = db.session.query(Fines).filter(Fines.loan_id == loan.loan_id, paid=False).first()
        if fines_entry:
            # Update existing entry
            fines_entry.fine_amt = fine_amount
        else:
            # Create a new entry if it doesn't exist
            new_fines_entry = Fines(loan_id=loan.loan_id, fine_amt=fine_amount, paid=False)
            db.session.add(new_fines_entry)
    # get the date of today
    today = date.today()
    # Update estimated fines for overdue books that are still out
    overdue_loans_still_out = db.session.query(BookLoan).filter(
        BookLoan.due_date < today, BookLoan.date_in is None
    ).all()
    for loan in overdue_loans_still_out:
        # Calculate the number of days overdue
        days_overdue = (today - loan.due_date).days
        # Calculate the estimated fine amount based on the rate of $0.25/day
        estimated_fine_amount = days_overdue * 0.25
        # Update the fine_amt in the Fines table for the corresponding loan_id
        fines_entry = db.session.query(Fines).filter(Fines.loan_id == loan.loan_id).first()
        if fines_entry:
            # Update existing entry
            fines_entry.fine_amt = estimated_fine_amount
        else:
            # Create a new entry if it doesn't exist
            new_fines_entry = Fines(loan_id=loan.loan_id, fine_amt=estimated_fine_amount, paid=False)
            db.session.add(new_fines_entry)
    # Commit the changes to the database
    db.session.commit()
    
    # query for all the unpaid loans
    fines_unpaid = db.session.query(Fines).filter(Fines.paid == False).all()
    # create a list of lan id of loans queried above
    unpaid_loan_ids = [fine.loan_id for fine in fines_unpaid]
    # query for unpaid loans that has date_in value
    unpaid_fines_in = db.session.query(BookLoan).filter(BookLoan.loan_id.in_(unpaid_loan_ids), BookLoan.date_in is not None).all()
    # query for unpaid loans that doesn't have date_in value
    unpaid_fines_out = db.session.query(BookLoan).filter(BookLoan.loan_id.in_(unpaid_loan_ids), BookLoan.date_in is None).all()
    # query for paid loans
    paid_fines = db.session.query(Fines).filter(Fines.paid == True).all()
    # display the fine page
    return render_template("fines.html", unpaid_fines_in=unpaid_fines_in, unpaid_fines_out=unpaid_fines_out, paid_fines=paid_fines)

# Handle the fine payment
@app.route('/payment/<id>', methods=['GET', 'POST'])
def payment(id):
    fine = db.session.query(Fines).filter(Fines.loan_id == id).first()
    entered_amount = 0.0
    # create a form object that takes care of payment submission
    form = PaymentForm()
    # validate if the form is at least filled in with some payment amount
    if form.validate_on_submit():
        # get the payment amount this user typed in
        entered_amount = form.amount.data
        # validate if this payment is full
        if entered_amount != float(fine.fine_amt):
            # indicate this user that the payment amount has to be exact
            flash('Amount does not match the fine amount.', 'error')
        else:
            # update this fine instance to be paid
            fine.paid = True
            # commit the change to the database
            db.session.commit()
            # pass the loan id of this fine to recepit() below
            session['loan_id'] = fine.loan_id
            # direct user to recipt page
            return redirect(url_for('receipt'))
    # display payment page
    return render_template("payment.html", fine=fine, form=form)

@app.route('/receipt', methods=['GET'])
def receipt():
    # get the lona id of the fine that have jsut been paid above
    loan_id = session.get('loan_id', [])
    # display receipt page
    return render_template("receipt.html", loan_id=loan_id)

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
    paid = db.Column(db.Boolean, nullable=False)
    db.ForeignKeyConstraint(['loan_id'], ['book_loans.loan_id'])

# Create a database named 'library_db'
def create_database():
    db_params = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': db_pass,
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
