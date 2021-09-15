from flask_wtf import FlaskForm
from wtforms import SelectField, TextField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

class AddHours(FlaskForm):

     def check_legnth(form, field):
          hours = str(field.data)
          print(hours)
          if hours[::-1].find('.') > 2:
               raise ValidationError("Hours amounts cannon have more than two decimal places.")

     description = TextField('Description', validators=[DataRequired(), Length(max=100)])
     hours = DecimalField('Hours', places = 2, validators=[DataRequired(), check_legnth])
     group = SelectField("Group", validators=[DataRequired()])
     teacher = SelectField("Teacher", validators=[DataRequired()])
     date  = DateField('Date Completed', format='%d/%m/%y', validators=[DataRequired()])
     submit = SubmitField("Log Hours", validators=[DataRequired()])