from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField
from wtforms.validators import DataRequired

class BorrowerForm(FlaskForm):
    ssn = StringField("SSN", validators=[DataRequired()])
    bname = StringField("Name", validators=[DataRequired()])
    address = StringField("Address", validators=[DataRequired()])
    phone = StringField("Phone", validators=[DataRequired()])
    submit = SubmitField("Register")
    
class PaymentForm(FlaskForm):
    amount = IntegerField("Amount")
    submit = SubmitField("Pay")
    
class SearchForm(FlaskForm):
    searched = StringField("Search", validators=[DataRequired()])
    submit = SubmitField("Search")