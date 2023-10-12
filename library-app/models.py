
# this file was generated with sqlacodegen

from typing import List, Optional

from sqlalchemy import Boolean, CHAR, CheckConstraint, Column, Date, ForeignKeyConstraint, Integer, Numeric, \
    PrimaryKeyConstraint, Table, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import decimal


class Base(DeclarativeBase):
    pass


class Authors(Base):
    __tablename__ = 'authors'
    __table_args__ = (
        PrimaryKeyConstraint('author_id', name='authors_pkey'),
    )

    author_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)

    book: Mapped[List['Book']] = relationship('Book', secondary='book_authors', back_populates='author')


class Book(Base):
    __tablename__ = 'book'
    __table_args__ = (
        PrimaryKeyConstraint('isbn', name='book_pkey'),
    )

    isbn: Mapped[str] = mapped_column(CHAR(13), primary_key=True)
    title: Mapped[str] = mapped_column(Text)

    author: Mapped[List['Authors']] = relationship('Authors', secondary='book_authors', back_populates='book')
    book_loans: Mapped[List['BookLoans']] = relationship('BookLoans', back_populates='book')


class Borrower(Base):
    __tablename__ = 'borrower'
    __table_args__ = (
        CheckConstraint('ssn >= 100000000 AND ssn <= 999999999', name='borrower_ssn_check'),
        PrimaryKeyConstraint('card_id', name='borrower_pkey'),
        UniqueConstraint('ssn', name='borrower_ssn_key')
    )

    card_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ssn: Mapped[int] = mapped_column(Integer)
    bname: Mapped[str] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)

    book_loans: Mapped[List['BookLoans']] = relationship('BookLoans', back_populates='card')


t_book_authors = Table(
    'book_authors', Base.metadata,
    Column('author_id', Integer, primary_key=True, nullable=False),
    Column('isbn', CHAR(13), primary_key=True, nullable=False),
    ForeignKeyConstraint(['author_id'], ['authors.author_id'], name='book_authors_author_id_fkey'),
    ForeignKeyConstraint(['isbn'], ['book.isbn'], name='book_authors_isbn_fkey'),
    PrimaryKeyConstraint('author_id', 'isbn', name='book_authors_pkey')
)


class BookLoans(Base):
    __tablename__ = 'book_loans'
    __table_args__ = (
        ForeignKeyConstraint(['card_id'], ['borrower.card_id'], name='book_loans_card_id_fkey'),
        ForeignKeyConstraint(['isbn'], ['book.isbn'], name='book_loans_isbn_fkey'),
        PrimaryKeyConstraint('loan_id', name='book_loans_pkey')
    )

    loan_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    isbn: Mapped[str] = mapped_column(CHAR(13))
    card_id: Mapped[int] = mapped_column(Integer)
    date_out: Mapped[datetime.date] = mapped_column(Date)
    due_date: Mapped[datetime.date] = mapped_column(Date)
    date_in: Mapped[Optional[datetime.date]] = mapped_column(Date)

    card: Mapped['Borrower'] = relationship('Borrower', back_populates='book_loans')
    book: Mapped['Book'] = relationship('Book', back_populates='book_loans')


class Fines(BookLoans):
    __tablename__ = 'fines'
    __table_args__ = (
        ForeignKeyConstraint(['loan_id'], ['book_loans.loan_id'], name='fines_loan_id_fkey'),
        PrimaryKeyConstraint('loan_id', name='fines_pkey')
    )

    loan_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fine_amt: Mapped[decimal.Decimal] = mapped_column(Numeric(8, 2))
    paid: Mapped[bool] = mapped_column(Boolean)
