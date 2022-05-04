from flask import Blueprint, render_template, redirect, url_for,request,flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import login_user, logout_user, login_required, current_user
from .models import users, pass_recovery, email_verification, login_history
from . import db
from .sendEmail import sendMail, sendMailForVerification
auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    if not current_user.is_authenticated:
        return render_template('login.html')
    else:
        return render_template('dashboard2.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = users.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)

    # Add record to login_history table
    user = users.query.filter_by(email=email).first()
    history = login_history(id=user.id, login_datetime=datetime.now())
    db.session.add(history)
    db.session.commit()

    return render_template('dashboard2.html')
    #return redirect(url_for('main.dashboard2'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    jobtitle = request.form.get('jobtitle')
    country = request.form.get('country')
    tnc = request.form.get('tnc')

    if not tnc:
        flash('Please accept terms and conditions')
        return redirect(url_for('auth.signup'))

    user = users.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists. Please go to login page')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = users(fullname=fullname,
                     email=email,
                     name=name,
                     password=generate_password_hash(password, method='sha256'),
                     jobtitle=jobtitle,
                     country=country,
                     emailverified=0,
                     created_at=datetime.now())

    # Add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    sendMailForVerification(email)
    flash('Link has been sent to your email for verification','success')
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/resetPass')
def resetPass():
    return render_template('reset_password.html')

@auth.route('/resetPass',methods=['POST'])
def resetPass_old():
    email = request.form.get('email')

    if email == '':
        flash('Please enter email address')
        return redirect(url_for('auth.resetPass'))

    sendMail(email)

    flash('Link to reset password has been send to your email','success')
    return redirect(url_for('auth.login'))

@auth.route('/updatePassword/<token>')
def updatePassword(token):
    return render_template('update_password.html',token = token)

@auth.route('/updatePassword', methods=['POST'])
def updatePassword_post():
    token = request.form.get('token')
    new = request.form.get('newpassword')
    confirm = request.form.get('confirmpassword')

    if new is '' or confirm is '':
        flash('Please enter all fields')
        return redirect(url_for('auth.updatePassword',token))

    passrecovery = pass_recovery.query.filter_by(token=token).first()

    if not passrecovery:
        flash('Invalid user')
        return redirect(url_for('auth.login'))

    now = datetime.now()
    created = passrecovery.created
    diff = (now - created).total_seconds() / 60.0

    if diff >= 10 or passrecovery.status != 0:
        passrecovery.status = 2
        passrecovery.updated = now
        db.session.commit()
        flash('Link expired, Please resend link again')
        return redirect(url_for('auth.resetPass'))

    user = users.query.filter_by(email=passrecovery.email).first()

    if not user:
        flash('Invalid user')
        return redirect(url_for('auth.login'))

    user.password = generate_password_hash(new)

    passrecovery.status = 1
    passrecovery.updated = now
    db.session.commit()
    flash('Password updated successfully','success')
    return redirect(url_for('auth.login'))

@auth.route('/verifyEmail/<token>')
def verifyEmail(token):
    message = ''
    if token is not '':
        verification = email_verification.query.filter_by(token=token).first()
        if not verification:
            message = 'Not verified. Please try again'
        else:
            now = datetime.now()
            created = verification.created
            diff = (now - created).total_seconds() / 60.0

            if diff >= 10 or verification.status != 0:
                verification.status = 2
                verification.updated = now
                db.session.commit()
                message = 'Link expired, Please resend link again'
            else:
                user = users.query.filter_by(email=verification.email).first()

                if not user:
                    message = 'User not found'
                else:
                    user.emailverified = 1

                    verification.status = 1
                    verification.updated = now
                    db.session.commit()
                    message = 'success'
    else:
        message = 'Not verified. Please try again'

    return render_template('verify_email.html',message = message)

@auth.route('/resendVerify')
@login_required
def resendVerify():
    email = current_user.email
    sendMailForVerification(email)
    flash('Link has been sent to your email for verification','success')
    return redirect(url_for('main.profile'))
