from service import db, login, app
from flask_login import UserMixin
from datetime import datetime
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    firstname = db.Column(db.String(64), index=True, nullable=False)
    lastname = db.Column(db.String(64), index=True, nullable=False)
    nickname = db.Column(db.String(64), index=True)
    last_updated_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    host_groups = db.relationship('Group', backref='host', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def get_full_name(self):
        return self.firstname + ' ' + self.lastname

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(user_id)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(120), index=True, unique=True, nullable=False)
    rsvp_close_date = db.Column(db.Date, index=True, nullable=False)
    reveal_date = db.Column(db.Date, index=True, nullable=False)
    budget = db.Column(db.Float, index=True)
    host_join = db.Column(db.Boolean, index=True)
    last_updated_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    preferences = db.relationship('Preference', backref='group', lazy='dynamic')
    members = db.relationship('GroupMember', backref='group', lazy='dynamic')

    def __repr__(self):
        return '<Group {}>'.format(self.groupname)

    def get_all_member_emails(self):
        current_members = self.members.all()
        current_emails = []
        for member in current_members:
            current_emails.append(member.member_email)
        if self.host_join:
            current_members.append(self.host.email)
        return current_emails

    def get_all_signup_member_emails(self):
        current_members = self.members.all()
        current_emails = []
        for member in current_members:
            if GroupMember.group_signup_status(self.id, member.member_email):
                current_emails.append(member.member_email)
        if self.host_join and GroupMember.group_signup_status(self.id, self.host.email):
            current_members.append(self.host.email)
        return current_emails

    def if_match_set(self):
        current_preferences = self.preferences.all()
        match_set = True
        for current_preference in current_preferences:
            if not current_preference.match:
                match_set = False
                break
        return match_set

    @staticmethod
    def check_group_member(group_name, email):
        current_group = Group.query.filter_by(groupname=group_name).first()
        current_emails = current_group.get_all_member_emails()
        if email in current_emails:
            return True
        else:
            return False


class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    member_email = db.Column(db.String(120), index=True, nullable=False)

    def __repr__(self):
        return '<GroupMember {}, {}>'.format(self.group_id, self.member_email)

    @staticmethod
    def signup_status(member_email):
        user = User.query.filter_by(email=member_email).first()
        if user:
            return True
        else:
            return False

    @staticmethod
    def group_signup_status(group_id, member_email):
        user = User.query.filter_by(email=member_email).first()
        if user:
            preferences = user.user_preferences.filter_by(group_id=group_id).first()
            if preferences:
                return True
        return False


class Preference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    first_preference = db.Column(db.String(500), index=True)
    second_preference = db.Column(db.String(500), index=True)
    third_preference = db.Column(db.String(500), index=True)
    match_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_updated_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #this is the many side, so uselist=False
    match = db.relationship("User", backref=db.backref("match_preferences", lazy='dynamic'), foreign_keys=[match_id], uselist=False)
    user = db.relationship("User", backref=db.backref("user_preferences", lazy='dynamic'), foreign_keys=[user_id], uselist=False)

    def __repr__(self):
        return '<Preference {}, {}>'.format(self.group_id, self.user_id)