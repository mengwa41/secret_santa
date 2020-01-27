from flask import render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from service import db
from service.main import bp
from service.main.forms import EditProfileForm, EditPasswordForm, InviteForm, AddMember, RemoveMember, PreferenceForm
from service.models import User, Group, GroupMember, Preference
from service.email import send_invite_email, send_reveal_email
import datetime
from helpers.santa_shuffle import get_santa

# profile
@bp.route("/user/self")
@login_required
def user():
    return render_template('profile/user.html')


@bp.route('/user/self/profile/edit', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.nickname = form.nickname.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile changes have been saved.')
        return redirect(url_for('main.user'))
    elif request.method == 'GET':
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.nickname.data = current_user.nickname
        form.email.data = current_user.email
    return render_template('profile/profile.html', title='Edit Profile',
                           form=form)


@bp.route('/user/self/account/edit', methods=['GET', 'POST'])
@login_required
def account():
    form = EditPasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password_new.data)
        db.session.commit()
        flash('Your password changes have been saved.')
        return redirect(url_for('main.user'))
    return render_template('profile/account.html', title='Edit Account',
                           form=form)


@bp.route('/user/self/groups', methods=['GET', 'POST'])
@login_required
def groups():
    host_groups = current_user.host_groups.all();
    current_group_members = GroupMember.query.filter_by(member_email=current_user.email).all()
    current_groups = []
    if len(current_group_members) != 0:
        for member in current_group_members:
            current_groups.append(member.group)
    if len(current_groups) == 0:
        print('You are currently not part of any groups.')
    # TO FIX
    return render_template('profile/groups.html', title='Groups', today = datetime.date.today(), user=current_user,
                           host_groups=host_groups, groups=current_groups, sign_up_func=GroupMember.group_signup_status)


# basic pages
@bp.route('/index')
def index():
    """
    header, initial page
    :return: the rendered form
    """
    return render_template('welcome.html')


@bp.route('/confirm')
def confirm():
    """
    header, used with flash to show confirmation or error
    :return: the rendered form
    """
    return render_template('header.html', title='Confirm')


# main functions
@bp.route('/invite', methods=['GET', 'POST'])
@login_required
def invite():
    """
    for host to invite people
    :return: the rendered form
    """
    form = InviteForm()
    if form.validate_on_submit():
        # add the new group
        group = Group(groupname=form.group.data, rsvp_close_date=form.rsvp_close_date.data,
                      reveal_date=form.reveal_date.data, host=current_user, budget=form.budget.data)
        db.session.add(group)
        db.session.commit()
        # add group members
        members = form.members.data.split(';')
        invited_member_size = len(members)
        if form.host_join.data:
            members.append(current_user.email)
        for member in members:
            group_member = GroupMember(group=group, member_email=member)
            db.session.add(group_member)
            db.session.commit()
        # send emails
        host_name = current_user.get_full_name()
        send_invite_email(members, host_name, form.group.data, form.rsvp_close_date.data)
        print('Sent invitation email to {} of {}'.format(form.members.data, form.group.data))
        flash('You have invited {} member(s) to join group {}'.format(invited_member_size, form.group.data))
        return redirect(url_for('main.confirm'))
    return render_template('invite.html', title='Invite', form=form)


@bp.route('/<group_name>/members', methods=['GET', 'POST'])
@login_required
def current_member(group_name):
    """
    for host to invite people
    :return: the rendered form
    """
    current_group = Group.query.filter_by(groupname=group_name).first()
    # check if requested by the host
    host = current_group.host
    if host.id != current_user.id:
        flash('Only the host is allowed to invite people to join group.')
        return redirect(url_for('main.index'))
    members = current_group.get_all_member_emails()
    signup_members = current_group.get_all_signup_member_emails()
    return render_template('current_members.html', title='Invite', group=group_name, members=members, signup_members=signup_members)


@bp.route('/<group_name>/members/add', methods=['GET', 'POST'])
@login_required
def add_member(group_name):
    """
    for host to invite people
    :return: the rendered form
    """
    form = AddMember()
    current_group = Group.query.filter_by(groupname=group_name).first()
    # check if requested by the host
    host = current_group.host
    if host.id != current_user.id:
        flash('Only the host is allowed to invite people to join group.')
        return redirect(url_for('main.index'))
    # cannot add after rsvp close date
    if datetime.date.today() >= current_group.rsvp_close_date:
        flash('We are sorry but the sign up for group {} has already closed.'.format(group_name))
        return redirect(url_for('main.index'))
    if form.validate_on_submit():
        # check if user already in group
        members = current_group.get_all_member_emails()
        if form.email.data in members:
            flash('{} has already been invited to group {}'.format(form.email.data, group_name))
            return redirect(url_for('main.index'))
        # add group members
        group_member = GroupMember(group=current_group, member_email=form.email.data)
        db.session.add(group_member)
        db.session.commit()
        # send emails
        host_name = current_user.get_full_name()
        send_invite_email([form.email.data], host_name, group_name, current_group.rsvp_close_date)
        print('Sent invitation email to {} of {}'.format(form.email.data, group_name))
        flash('You have invited {} to join group {}'.format(form.email.data, group_name))
        return redirect(url_for('main.confirm'))
    return render_template('add_member.html', title='Invite', group=group_name, form=form)


@bp.route('/<group_name>/members/remove', methods=['GET', 'POST'])
@login_required
def remove_member(group_name):
    """
    for host to invite people
    :return: the rendered form
    """
    form = RemoveMember()
    # cannot remove after rsvp close date
    current_group = Group.query.filter_by(groupname=group_name).first()
    # check if requested by the host
    host = current_group.host
    if host.id != current_user.id:
        flash('Only the host is allowed to remove people to join group.')
        return redirect(url_for('main.index'))
    # cannot add after rsvp close date
    if datetime.date.today() >= current_group.rsvp_close_date:
        flash('We are sorry but the sign up for group {} has already closed.'.format(group_name))
        return redirect(url_for('main.index'))
    if form.validate_on_submit():
        # check if user in group
        members = current_group.get_all_member_emails()
        if form.email.data not in members:
            flash('{} is not in the group {}'.format(form.email.data, group_name))
            return redirect(url_for('main.index'))
        # remove group members
        group_member = current_group.members.filter_by(member_email=form.email.data).first()
        db.session.delete(group_member)
        db.session.commit()
        flash('You have removed {} from group {}'.format(form.email.data, group_name))
        return redirect(url_for('main.confirm'))
    return render_template('remove_member.html', title='Invite', group=group_name, form=form)


@bp.route('/<group_name>/preference', methods=['GET', 'POST'])
@login_required
def preference(group_name):
    """
    for users to input their info and gift preferences
    :param group_name: group_name
    :return: the rendered form
    """
    current_group = Group.query.filter_by(groupname=group_name).first()
    # group validation
    if not Group.check_group_member(current_group.groupname, current_user.email):
        flash('Please double check your group name.')
        return redirect(url_for('main.index'))
    #reveal date check
    if datetime.date.today() >= current_group.rsvp_close_date:
        flash('We are sorry but the sign up for group {} has already closed.'.format(group_name))
        return redirect(url_for('main.index'))
    #load form
    current_preference = current_user.user_preferences.filter_by(group_id=current_group.id).first()
    form = PreferenceForm()
    if form.validate_on_submit():
        if current_preference:
            current_preference.first_preference = form.preference_first.data
            current_preference.second_preference = form.preference_second.data
            current_preference.third_preference = form.preference_third.data
            db.session.commit()
        else:
            new_preference = Preference(group=current_group, user_id=current_user.id, first_preference=form.preference_first.data,
                                    second_preference=form.preference_second.data, third_preference=form.preference_third.data)
            db.session.add(new_preference)
            db.session.commit()
        flash('Santa has received preferences of {} in group {}! You will find out the id of your secret santa on {}'.format(
                     current_user.username, current_group.groupname, current_group.reveal_date))
        return redirect(url_for('main.confirm'))
    else:
        if current_preference:
            form.preference_first.data = current_preference.first_preference
            form.preference_second.data = current_preference.second_preference
            form.preference_third.data = current_preference.third_preference
    return render_template('preference.html', title='Preference',
                           username=current_user.username, group=current_group.groupname,
                           close_date=current_group.rsvp_close_date, reveal_date=current_group.reveal_date,
                           form=form)


@bp.route('/<group_name>/reveal', methods=['GET', 'POST'])
@login_required
def reveal(group_name):
    """
    send secret santa results
    :return: the rendered form
    """
    current_group = Group.query.filter_by(groupname=group_name).first()
    # check if requested by the host
    host = current_group.host
    if host.id != current_user.id:
        flash('Only the host is allowed to see the match results.')
        return redirect(url_for('main.index'))
    # check if reveal date is met
    if datetime.date.today() < current_group.reveal_date:
        flash('Please be patient, reveal date is {}.'.format(current_group.reveal_date))
        return redirect(url_for('main.index'))
    # check if shuffle result is saved
    current_preferences = current_group.preferences.all()
    if not current_group.if_match_set():
        print('Generating secret santa match for group {}'.format(group_name))
        emails = current_group.get_all_signup_member_emails()
        santa_map = get_santa(emails)
        # set match in preference
        for current_preference in current_preferences:
            current_preference.match = User.query.filter_by(email=santa_map[current_preference.user.email]).first()
            db.session.commit()
            send_reveal_email(current_preference.user.email, current_group, current_preference.match.get_full_name(),
                              current_preference.first_preference, current_preference.second_preference,
                              current_preference.third_preference)
            print('Reveal email has been sent to {} for group {}'.format(current_preference.user.email, group_name))
    # show match results
    match_map = {}
    for current_preference in current_preferences:
        match_map[current_preference.user.get_full_name()] = current_preference.match.get_full_name()
    return render_template('group_results.html', title='Reveal', group=group_name, match_map=match_map)


@bp.route('/<group_name>/reveal/<user_name>', methods=['GET', 'POST'])
@login_required
def reveal_user(group_name, user_name):
    """
    secret santa result for group & user
    :return: the rendered form
    """
    curr_user = User.query.filter_by(username=user_name).first()
    curr_group = Group.query.filter_by(groupname=group_name).first()
    match = curr_user.user_preferences.filter_by(group_id=curr_group.id).first().match
    if not match:
        match_name = None
    else:
        match_name = match.get_full_name()
    return render_template('match_result.html', title='My match', group=group_name, match_name=match_name)