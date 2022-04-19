from flask import Blueprint, render_template,url_for, redirect,request
from flask.helpers import flash
from flask_login import login_required, current_user, logout_user
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('login.html')
    else:
        print("authenticated")
        return render_template('dashboard2.html')
        #return redirect(url_for('main.dashboard2'))

@main.route('/dashboard2')
@login_required
def dashboard2():
    email = current_user.email
    user = User.query.filter_by(email=email).first()
    user_obj = {'fullname':user.fullname, 'email':user.email,'name':user.name,'jobtitle':user.jobtitle,'country':user.country,'emailverified':user.emailverified}
    return render_template('dashboard2.html', user=user_obj)


@main.route('/profile')
@login_required
def profile():
    email = current_user.email
    user = User.query.filter_by(email=email).first()
    user_obj = {'fullname':user.fullname, 'email':user.email,'name':user.name,'jobtitle':user.jobtitle,'country':user.country,'emailverified':user.emailverified}
    return render_template('profile.html', user=user_obj)

@main.route('/changePass')
@login_required
def changePass():
    return render_template('change_password.html')


@main.route('/changePass', methods=['POST'])
@login_required
def changePass_post():
    old = request.form.get('oldpassword')
    new = request.form.get('newpassword')
    confirm = request.form.get('confirmpassword')

    if old == '' or new == '' or confirm == '':
        flash('Please enter all fields')
        return redirect(url_for('main.changePass'))

    if new != confirm:
        flash('Confirm password does not match')
        return redirect(url_for('main.changePass'))

    email = current_user.email
    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, old):
        flash('Invalid password.')
        return redirect(url_for('main.changePass'))

    user.password = generate_password_hash(new)

    db.session.commit()
    logout_user()
    flash('Password updated successfully, Please login again.','success')
    return redirect(url_for('auth.login'))


@main.route('/updateProfile', methods=['POST'])
@login_required
def updateProfile():
    fullname = request.form.get('fullname')
    name = request.form.get('name')
    jobtitle = request.form.get('jobtitle')
    country = request.form.get('country')

    email = current_user.email

    user = User.query.filter_by(email=email).first()
    user.fullname = fullname
    user.name = name
    user.jobtitle = jobtitle
    user.country = country

    db.session.commit()
    flash('Profile updated successfully.','success')
    return redirect(url_for('main.profile'))
