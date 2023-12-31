from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, SubmitField, SelectMultipleField, widgets, FloatField, \
    BooleanField
from wtforms.validators import DataRequired


class BorrowerForm(FlaskForm):
    ssn = StringField("SSN", validators=[DataRequired()])
    bname = StringField("Name", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    phone = StringField("Phone", validators=[DataRequired()])
    submit = SubmitField("Register")
    
class PaymentForm(FlaskForm):
    submit = SubmitField("Pay")
    
class SearchForm(FlaskForm):
    searched = StringField("Search", validators=[DataRequired()])
    submit = SubmitField("Search")

class CheckInSearchForm(FlaskForm):
    searched = StringField("Search", validators=[DataRequired()])
    search_isbn = BooleanField("ISBN")
    search_card_id = BooleanField("Card ID")
    search_bname = BooleanField("Borrower Name")
    submit = SubmitField("Search")

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class BookForm(FlaskForm):
    books = MultiCheckboxField('Label', choices=[])
    submit = SubmitField('Borrow')
    
class CheckOutForm(FlaskForm):
    card_id = IntegerField("Enter the Card ID", validators=[DataRequired()])
    submit = SubmitField('CheckOut')
    
class IsbnForm(FlaskForm):
    isbn = StringField("Enter the ISBN", validators=[DataRequired()])
    submit = SubmitField('Checkout')