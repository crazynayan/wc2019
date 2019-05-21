from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField
from wtforms.validators import InputRequired, NumberRange, ValidationError, DataRequired
from app.models import User


class BidForm(FlaskForm):
    amount = IntegerField('', validators=[InputRequired('Bid is required.'), NumberRange(min=0, max=User.INITIAL_BUDGET)])
    submit = SubmitField('Submit')

    def __init__(self, balance, *args, **kwargs):
        self.balance = balance
        super().__init__(*args, **kwargs)

    def validate_amount(self, amount):
        if isinstance(amount.data, int):
            if amount.data > self.balance:
                raise ValidationError(f'Please do not bid more than your balance of \u20b9 {self.balance} lacs.')


class SearchForm(FlaskForm):
    q = StringField('Search tags', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super().__init__(*args, **kwargs)
