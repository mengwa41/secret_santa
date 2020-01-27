from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, SubmitField, DateField, PasswordField, FloatField, BooleanField
from wtforms.widgets import TextArea
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from service.models import User
from datetime import date


class EditProfileForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    nickname = StringField('Nickname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Save Edit')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None and user.email != current_user.email:
            raise ValidationError('Please use a different email address.')


class EditPasswordForm(FlaskForm):
    password = PasswordField('Old Password', validators=[DataRequired()])
    password_new = PasswordField('New Password', validators=[DataRequired()])
    password_new1 = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password_new')])
    submit = SubmitField('Save New Password')

    def validate_password(self, password):
        if not current_user or not current_user.check_password(password.data):
            raise ValidationError('Old password is not valid.')


class InviteForm(FlaskForm):
    group = StringField('Group Name', validators=[DataRequired()])
    rsvp_close_date = DateField('RSVP Close Date', validators=[DataRequired()])
    reveal_date = DateField('Secret Santa Reveal Date', validators=[DataRequired()])
    budget = FloatField('Gift Budget (US $)', validators=[DataRequired()] )
    members = StringField('Email of members (separated by ;)', validators=[DataRequired()], widget=TextArea())
    host_join = BooleanField('Will you join the fun?')
    submit = SubmitField('Invite')

    def validate_rsvp_close_date(self, rsvp_close_date):
        if rsvp_close_date.data <= date.today():
            raise ValidationError('RSVP close date needs to be later than today.')
        if self.reveal_date.data and self.reveal_date.data < rsvp_close_date.data:
            raise ValidationError('RSVP close date needs to be before reveal date.')


    def validate_reveal_date(self, reveal_date):
        if reveal_date.data <= date.today():
            raise ValidationError('Reveal date needs to be later than today.')
        if self.rsvp_close_date.data and reveal_date.data < self.rsvp_close_date.data:
            raise ValidationError('Reveal date needs to be before RSVP close date.')


class AddMember(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Invite Email')


class RemoveMember(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Notify Email')


class PreferenceForm(FlaskForm):
    preference_first = StringField('Preference One', widget=TextArea())
    preference_second = StringField('Preference Two', widget=TextArea())
    preference_third = StringField('Preference Three', widget=TextArea())
    submit = SubmitField('Submit')


class EmailRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    group = StringField('Group Name', validators=[DataRequired()])
    submit = SubmitField('Send Email')
