from flask_wtf import FlaskForm
from wtforms import SelectField, TextField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired

class AddHours(FlaskForm):
     description = TextField('Description', validators=[DataRequired()])
     hours = DecimalField('Hours', places = 2, validators=[DataRequired()])
     group = SelectField("Group", validators=[DataRequired()])
     teacher = TextField("Teacher", validators=[DataRequired()])
     date  = DateField('Date Completed', format='%d/%m/%y', validators=[DataRequired()])
     submit = SubmitField("Log Hours", validators=[DataRequired()])