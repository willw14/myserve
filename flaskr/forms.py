from flask_wtf import FlaskForm
from wtforms import SelectField, TextField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired
from flask_login import current_user

class AddHours(FlaskForm):
     description = TextField('Description', validators=[DataRequired()])
     hours = DecimalField('Hours', validators=[DataRequired()])
     group = SelectField("Group", coerce=int, validators=[DataRequired()])
     date  = DateField('Date Completed', format='%d/%m/%y', validators=[DataRequired()])
     submit = SubmitField("Log Hours", validators=[DataRequired()])