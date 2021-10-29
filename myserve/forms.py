from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField, TextField, DecimalField, DateField, SubmitField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange
import datetime


def validate_legnth(form, field):
    """checks that the user has not entered an hours amount to more than two d.p."""
    hours = str(field.data)
    if hours[::-1].find('.') > 2:
        raise ValidationError(
            "Hours amounts cannot have more than two decimal places.")


def validate_date(form, field):
    """checks that a date is not in the future i.e. the service hasn't happened yet,
    and that the date isn't from a previous year"""
    if field.data > datetime.date.today() or field.data.year < datetime.date.today().year:
        raise ValidationError(
            "Please enter a date that is within this year and not in the future.")


class AddHours(FlaskForm):
    description = TextField('Description', validators=[DataRequired(), Length(
        max=100, message="Please enter a description with less than 100 characters.")])
    hours = DecimalField(
        'Hours',
        validators=[
            DataRequired(),
            validate_legnth,
            NumberRange(
                min=0,
                max=100,
                message='Please enter a number between 0 and 100')])
    group = SelectField("Group", validators=[DataRequired()])
    teacher = SelectField("Teacher", validators=[DataRequired()])
    date = DateField(
        'Date Completed',
        format='%d/%m/%y',
        validators=[
            DataRequired(
                message="Please enter a valid date in the format dd/mm/yy."),
            validate_date])
    submit = SubmitField("Log Hours")
    delete = SubmitField("Delete")


class MultiCheckboxField(SelectMultipleField):
    """creates a multiple select that utilises checkboxes"""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class JoinGroups(FlaskForm):
    groups = MultiCheckboxField('Select Groups')
    submit = SubmitField("Save")


class CreateGroup(FlaskForm):
    name = TextField(
        'Group Name',
        validators=[
            DataRequired(),
            Length(
                max=40,
                message="Please enter a group name with less than 40 characters.")])
    save = SubmitField("Create")


class UserUpload(FlaskForm):
    file = FileField(
        'Upload File',
        validators=[
            FileRequired(),
            FileAllowed(
                ['csv'],
                'Please upload a .csv file.')])
    upload = SubmitField("Upload", validators=[])
