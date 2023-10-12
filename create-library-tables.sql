CREATE TABLE IF NOT EXISTS BOOK (
	Isbn CHAR(13) PRIMARY KEY NOT NULL,
	Title TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS AUTHORS (
	Author_id INT PRIMARY KEY NOT NULL,
	Name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS BOOK_AUTHORS (
	Author_id INT NOT NULL,
	Isbn CHAR(13) NOT NULL,
	PRIMARY KEY (Author_id, Isbn),
	FOREIGN KEY (Author_id) REFERENCES AUTHORS(Author_id),
	FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn)
);
CREATE TABLE IF NOT EXISTS BORROWER (
	Card_id INT PRIMARY KEY NOT NULL,
	Ssn INT NOT NULL UNIQUE,
	Bname TEXT NOT NULL,
	Address TEXT,
	Phone TEXT,
	CHECK (Ssn >= 100000000 AND Ssn <= 999999999) -- SSN must be a 9-digit number
);
CREATE TABLE IF NOT EXISTS BOOK_LOANS (
	Loan_id INT PRIMARY KEY NOT NULL,
	Isbn CHAR(13) NOT NULL,
	Card_id INT NOT NULL,
	Date_out DATE NOT NULL,
	Due_date DATE NOT NULL,
	Date_in DATE,
	FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn),
	FOREIGN KEY (Card_id) REFERENCES BORROWER(Card_id)
);
CREATE TABLE IF NOT EXISTS FINES (
	Loan_id INT PRIMARY KEY NOT NULL,
	Fine_amt DECIMAL(8,2) NOT NULL, -- assumes that a fine isn't ever going to get above 999,999.99 
	Paid BOOLEAN NOT NULL,
	FOREIGN KEY (Loan_id) REFERENCES BOOK_LOANS(Loan_id)
);