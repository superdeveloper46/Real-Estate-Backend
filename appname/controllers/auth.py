from flask import Blueprint, session, request, jsonify, make_response

import os

from appname.models import db
from appname.models.user import User
from appname.mailers.auth import ResetPassword
from appname.mailers.auth import WelcomeEmail
from appname.extensions import limiter
from appname.utils.slack import send_slack_notification # import the Slack notification function

# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)

@auth.route("/api/auth/login", methods=["POST"])
@limiter.limit("20/minute")
def login():
    # gets email and password
    params = request.get_json()
    email, password = params['email'], params['password']
  
    user = User.query.filter_by(email=email).first()

    if not user:
        # returns 404 if user doesn't exist
        return make_response(jsonify(
            access_token='unknown',
            status=404
        ), 200)
  
    if user.check_password(password):
        # generates the JWT Token
        access_token = jwt.encode({
            'id': user.id,
            'exp' : datetime.utcnow() + timedelta(hours = 1)
        }, os.getenv('SECRET_KEY'))
        
        refresh_token = jwt.encode({
            'id': user.id,
            'exp' : datetime.utcnow() + timedelta(hours = 24)
        }, os.getenv('SECRET_KEY'))
        
        # successfully logged in

        # send slack alert
        send_slack_notification(channel='#user-app-activity', text=f'User {user.full_name} ({user.email}) logged in.')

        return make_response(jsonify(
            access_token=access_token.decode('UTF-8'),
            refresh_token=refresh_token.decode('UTF-8'),
            userName=user.full_name,
            status=201
        ), 201)
    else:
        # returns 403 if password is wrong
        return make_response(jsonify(
            access_token='unknown',
            status=403
        ), 200)

@auth.route("/api/auth/signup", methods=["POST"])
@limiter.limit("10/minute")
def signup():
    # gets email and password
    params = request.get_json()
    email, name, password = params['email'], params['name'], params['password']

    # checking for existing user
    user = User.query.filter_by(email = email).first()
    if not user:
        # database ORM object
        user = User(
            email = email,
            name = name,
            password = password
        )
        # insert user
        db.session.add(user)
        db.session.commit()

        # generates the JWT Token
        access_token = jwt.encode({
            'id': user.id,
            'exp' : datetime.utcnow() + timedelta(hours = 1)
        }, os.getenv('SECRET_KEY'))
        
        refresh_token = jwt.encode({
            'id': user.id,
            'exp' : datetime.utcnow() + timedelta(hours = 24)
        }, os.getenv('SECRET_KEY'))

        # successfully logged in - send Slack notification
        send_slack_notification(channel='#user-app-activity', text=f'New user {user.full_name} ({user.email}) signed up.') # Slack alert for signup

        
        # welcom email
        WelcomeEmail(user).send()
        return make_response(jsonify(
            access_token=access_token.decode('UTF-8'),
            refresh_token=refresh_token.decode('UTF-8'),
            userName=user.full_name,
            status=201
        ), 201)
        
        
    else:
        # returns 202 if user already exists
        return make_response(jsonify(
            token='unknown',
            status=202
        ), 202)

@auth.route("/api/auth/request_reset_password", methods=["POST"])
@limiter.limit("20/hour")
def request_password_reset():
    # gets registered email
    params = request.get_json()
    email = params['email']

    user = User.query.filter_by(email=email).first()
    if user:
        try:
            # generate JWT token
            jwt_token = jwt.encode({
                'email': email,
                'exp' : datetime.utcnow() + timedelta(minutes = 30)
            }, os.getenv('SECRET_KEY'))
            auth_token=jwt_token.decode('UTF-8')
            # save reset password auth token to db
            user.update_auth_token(auth_token)
            # send a password reset email
            response = ResetPassword(user).send(auth_token)
            # successfully signed up
            return make_response(jsonify({'status': 200}), 200)
        except:
            # unexpected error occurred
            return make_response(jsonify({'status': 'error'}), 200)
    else:
        # That email doesn't appear to be registered
        return make_response(jsonify({'status': 404}), 200)

@auth.route("/api/auth/reset_password", methods=["POST"])
@limiter.limit("20/hour")
def reset_password():
    # get new password and reset password token
    params = request.get_json()
    new_password, token = params['password'], params['token']

    try:
        # decoding the payload to fetch the stored details
        data = jwt.decode(token, os.getenv('SECRET_KEY'))
        email, exp = data['email'], data['exp']
        expiredDatetime = datetime.utcfromtimestamp(exp)

        user = User.query.filter_by(email=email).first()
        if user:
            if user.auth_token != token:
                # invalid token provided
                return make_response(jsonify({'status': 403}), 200)
            if datetime.utcnow() >= expiredDatetime:
                # expired token provided
                return make_response(jsonify({'status': 408}), 200)

            user.update_password(new_password)
            user.update_auth_token('')
            # successfuly updated password
            return make_response(jsonify({'status': 200}), 200)
        else:
            # the user doesn't exist
            return make_response(jsonify({'status': 404}), 200)
    except:
        # unexpected internal server error
        return make_response(jsonify({'status': 500}), 200)


# @auth.route("/confirm/<string:code>")
# def confirm(code):
#     if not constants.REQUIRE_EMAIL_CONFIRMATION:
#         abort(404)

#     try:
#         email = token.decode(code, salt=constants.EMAIL_CONFIRMATION_SALT)
#     except Exception:
#         email = None

#     if not email:
#         # TODO: Render a nice error page here.
#         return abort(404)

#     user = User.query.filter_by(email=email).first()
#     if not user:
#         return abort(404)
#     user.email_confirmed = True
#     db.session.commit()

#     if current_user == user:
#         flash('Succesfully confirmed your email', 'success')
#         return redirect(url_for("dashboard_home.index"))
#     else:
#         flash('Confirmed your email. Please login to continue', 'success')
#         return redirect(url_for("auth.login"))


# @auth.route("/auth/resend-confirmation", methods=["GET", "POST"])
# @limiter.limit("5/minute")
# @login_required
# def resend_confirmation():
#     if not constants.REQUIRE_EMAIL_CONFIRMATION:
#         abort(404)
#     if current_user.email_confirmed:
#         return redirect(url_for("dashboard_home.index"))

#     form = SimpleForm()
#     if form.validate_on_submit():
#         if ConfirmEmail(current_user).send():
#             flash(
#                 "Sent confirmation to {}".format(
#                     current_user.email),
#                 'success')
#         return redirect(url_for("dashboard_home.index"))

#     return render_template('auth/resend_confirmation.html', form=form)


# @auth.route("/reauth", methods=["GET", "POST"])
# def reauth():
#     form = LoginForm()

#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).one()
#         login_user(user)

#         flash("Re-authenticated successfully.", "success")
#         return redirect(request.args.get("next", url_for("user_settings.index")))
#     return render_template("reauth.html", form=form)

# @auth.route('/invite/<hashid:invite_id>/join')
# @login_required
# def join_team(invite_id):
#     invite = TeamMember.query.get(invite_id)
#     if not invite or invite.user != current_user:
#         return abort(404)

#     invite.activate(current_user.id)
#     return redirect(url_for("dashboard_home.index"))

# @auth.route('/join/<hashid:invite_id>/<string:secret>')
# @limiter.limit("20/minute")
# def invite_page(invite_id, secret):
#     invite = TeamMember.query.get(invite_id)
#     if not invite.invite_secret or invite.invite_secret != secret or invite.activated:
#         return abort(404)

#     if current_user.is_authenticated and invite.user == current_user:
#         return redirect(url_for(".join_team", invite_id=invite.id))

#     form = SignupForm(invite_secret=invite.invite_secret)
#     return render_template("auth/invite.html", form=form, invite=invite)