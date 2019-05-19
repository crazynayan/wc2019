from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField
from wtforms.validators import InputRequired, NumberRange, ValidationError
from app.models import User


class BidForm(FlaskForm):
    amount = IntegerField('', validators=[InputRequired('Bid is required.'), NumberRange(min=0, max=User.INITIAL_BUDGET)])
    submit = SubmitField('Submit')

    def __init__(self, balance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.balance = balance

    def validate_amount(self, amount):
        if isinstance(amount.data, int):
            if amount.data > self.balance:
                raise ValidationError(f'Please do not bid more than your balance of \u20b9 {self.balance} lacs.')
