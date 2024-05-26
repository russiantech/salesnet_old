from datetime import datetime
from flask import abort, current_app, session, jsonify, render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_
#from utils.time_ago import timeAgo
from web.extensions import bcrypt, socketio
from web.models import db, Role, User, Brand
from web.utils import notifyer, ip_adrs
from web.auth.forms import (SignupForm, SigninForm, UpdateMeForm, ForgotForm, ResetForm)
from web.utils.decorators import admin_or_current_user
from web.utils.providers import oauth2providers
from web.utils.decorators import db_session_management
from web.apis.tokens import hash_auth

#oauth implimentations
import secrets, requests
from urllib.parse import urlencode

from dotenv import load_dotenv
from os import getenv
load_dotenv()

auth = Blueprint('auth', __name__)

def hash_txt(txt):
    return bcrypt.generate_password_hash(txt).decode('utf-8') #use .encode('utf-8') to decode this

def handle_response(success, message, data=None, error_message=None, link=None):
    """ only success response should have data and be set to True. And  """
    response_data = {
        'success': success,
        'message': message,
    }
    #response_data['link'] = request.base_url
    if link:
        response_data['link'] = link
    if data:
        response_data['data'] = data
    if error_message:
        response_data['error_message'] = error_message

    return response_data

@auth.route("/send_sms", methods=['POST', 'GET'])
def send_sms():
    #data = request.get_json()
    phone_number = +2348138958645
    #order_id = data.get("order_id")
    """ Kindly wait for twillo to activate my account, so I can get the credentials """
    message = f"Thank you for your order! Your order ID is {phone_number}."
    
    success, response = notifyer.send_sms(phone_number, message)

    if success:
        return jsonify({"message": "Order confirmation SMS sent successfully."})
    else:
        return jsonify({"error": response}), 500
    

@auth.route("/signup", methods=['POST'])
@db_session_management
def signup():
        
    if not db.session.is_active:
        db.session.begin()

    referrer = request.referrer

    form = SignupForm()
    
    if current_user.is_authenticated:
        return jsonify(
            handle_response(
            True, f"Weldone {current_user.username}. You're signed in already.", 
            link=referrer)
            )

    if form.validate_on_submit():

        user = User.query.filter( or_( User.email==form.email.data, User.phone==form.phone.data, User.username==form.username.data) ).first()
        
        if user :
            return jsonify(handle_response(
                False, 'user validation failed',  
                error_message=f"seems there's someone having some of these details already.")
        )
                
        user = User(
            name=form.name.data, 
            username=form.username.data, 
            email=form.email.data, 
            phone=form.phone.data, 
            password=hash_txt(form.password.data), 
            ip =ip_adrs.user_ip()
            )
        
        db.session.add(user)

        """ if not db.session.is_active:
            db.session.commit()  """
        
        db.session.commit()

        db.session.flush()
        db.session.refresh(user) 

        #email.verify_email(user) if user else flash('Sorry, some issues while sending verification emails.', 'info')
        msg = 'sign-up success!. Try & get verified for a seamless experience, since we\'re unable to verify ur email/phone right now'
        #notifyer_phone = notifyer.send_sms(user.phone, msg)
        notifyer_email = notifyer.verify_email(user)
        #if not notifyer_phone and not notifyer_email:
        if not notifyer_email:
            return jsonify(handle_response(
                True, msg, link='#signin-modal', 
                error_message=f"Hey! {user.username}. could not send ur verification mail right now. Try & get verified for a seamless experience. ")
                )
        print(f"sms/email sent to ->{user.email}")
        return jsonify(handle_response(
                True, 'sign up success!!!', link='#signin-modal',
                error_message = f"weldone {user.username}. Confirm ur verification email/sms for seamless xperience.\
                You\'re now still able to connect with brands . friends . clients & products though")
                )
    #print(form.data, form.errors)
    return jsonify(
        handle_response( False, 'form validation failed', error_message=f"{form.errors}")
                )

#this route-initializes auth
@auth.route('/authorize/<provider>')
@db_session_management
def oauth2_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('auth.update', usrname=current_user.username))

    provider_data = oauth2providers.get(provider)
    if provider_data is None:
        abort(404)

    # generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    # create a query string with all the reqired OAuth2 parameters
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': url_for('auth.oauth2_callback', provider=provider, _external=True),
        'response_type': 'code',
        'scope': ' '.join(provider_data['scopes']), #scope/info or data you want, only email or more ...like photo etc
        'state': session['oauth2_state'],
    })

    # redirect the user to the OAuth2 provider authorization URL
    return redirect(provider_data['authorize_url'] + '?' + qs)

@auth.route('/callback/<provider>')
@db_session_management
def oauth2_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    provider_data = oauth2providers.get(provider)
    if provider_data is None:
        abort(404)

    # if there was an authentication error, flash the error messages and exit
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('main.index'))

    # make sure that the state parameter matches the one we created in the
    # authorization request
    if request.args['state'] != session.get('oauth2_state'):
        abort(401)

    # make sure that the authorization code is present
    if 'code' not in request.args:
        abort(401)

    # exchange the authorization code for an access token
    response = requests.post(provider_data['token_url'], data={
        'client_id': provider_data['client_id'],
        'client_secret': provider_data['client_secret'],
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('auth.oauth2_callback', provider=provider,
                                _external=True),
    }, headers={'Accept': 'application/json'})

    if response.status_code != 200:
        abort(401)
    oauth2_token = response.json().get('access_token')
    if not oauth2_token:
        abort(401)

    # use the access token to get the user's email address
    response = requests.get(
        provider_data['userinfo']['url'], 
        headers={'Authorization': 'Bearer ' + oauth2_token,
        'Accept': 'application/json',
    })
    if response.status_code != 200:
        abort(401)
        
    email = provider_data['userinfo']['email'](response.json())
    # find or create the user in the database
    user = db.session.scalar(db.select(User).where(User.email == email))
    if user is None:
        user = User(email=email, username=email.split('@')[0], password=hash_txt(secrets.token_urlsafe(5)), src=provider)
        db.session.add(user)
        db.session.commit()
        #//flush & refresh to get pdated user_id
        db.session.flush()
        db.session.refresh(user)
    # log the user in
    login_user(user)
    socketio.emit('signedin', {'user_id': user.id}) #emitting socket events to notify server/socket route that this person just logged-in, update/add them to socket service.
    # Emit the signal when a user is authenticated
    #user_authenticated.send(current_app._get_current_object(), user_id=user.id, socket_id=request.sid)

    return redirect(url_for('main.index'))

@auth.route("/signin", methods=['POST'])
@db_session_management
def signin():

    referrer = request.referrer

    if not db.session.is_active:
        db.session.begin()

    if not current_user.is_anonymous:
        #return redirect(url_for('main.index'))
        return jsonify(
            handle_response(
            True, 'signed in already!!!', link=referrer,
            error_message = f"Weldone {current_user.username}. You're signed in already.")
            )

    form = SigninForm()
    
    if form.validate_on_submit():
        user = User.query.filter( or_( User.email==form.signin.data, User.phone==form.signin.data, User.username==form.signin.data) ).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            user.online = True
            user.last_seen = datetime.utcnow()
            user.ip = ip_adrs.user_ip()
            
            if not db.session.is_active:
                db.session.commit() 
            #db.session.commit()
            login_user(user, remember=form.rememberme.data) #login_user(user)
            # Emit the signal when a user is authenticated
            #user_authenticated.send(current_app._get_current_object(), user_id=user.id, socket_id=request.sid)
            socketio.emit('is_authenticated', user.username)
            next_page = request.args.get('next')

            return jsonify(handle_response(
                    True, 'Sign-in success!!!', link=referrer,
                    error_message = f"welcome {user.username}. xperience sales. connect with brands . friends . clients & products.")
                    )
        else: 
            flash('Invalid Login Details. Try Again', 'danger')
            #return redirect(referrer)
            return jsonify(handle_response(
                False, 'Invalid login request', link=referrer,
                error_message=f"Your login details are not correct. Try again.")
            )
    #return render_template('auth/signin.html', title='Sign In', form=form)
    return jsonify(
        handle_response( False, 'form validation failed', error_message=f"{form.errors}")
                )
    
@auth.route("/signout", methods=['GET'])
@login_required
@db_session_management
def signout():
    
    if not db.session.is_active:
        db.session.begin()

    if not current_user.is_authenticated:
        return redirect(url_for('main.index')) 
    """ Disconnect from db before logging-out the user """
    username = current_user.username if current_user.is_authenticated else str(True)
    socketio.emit('is_anonymous', username) 
    print(f'is_anonymous emitted for {username} cos of log-out')
    current_user.online = False if current_user.is_authenticated else False
    db.session.commit()
    
    logout_user()

    return redirect(url_for('main.index'))

@auth.route("/<string:usrname>/update", methods=['GET', 'POST'])
@login_required
@admin_or_current_user()
@db_session_management
def update(usrname):
    usr = User.query.filter(User.username==usrname).first_or_404()
    form = UpdateMeForm()
    if usr.role:
        # Get the user's current role
        current_role = [ (r.id, r.type) for r in usr.role] or [('0', 'Not Granted')]
        other_roles = Role.query.filter( ~Role.id.in_(current_role[0]) if current_role[0] else None ).all() 

        choices = [ ( x[0], x[1]) for x in current_role] or [('0', 'nothing')] #if current_role else [ '', 'Nothing']
        choices.extend( (role.id, role.type) for role in other_roles) if current_user.is_admin() else None
        # Set choices for the form's role field
        form.role.choices = choices
    else:
        pass
    
    handles = usr.socials # Retrieve existing dictionary or create a new one

    if form.validate_on_submit():
        usr.name = form.name.data
        usr.username = form.username.data
        usr.email = form.email.data
        usr.phone = form.phone.data
        usr.gender = form.gender.data
        usr.acct_no = form.acct_no.data
        usr.bank = form.bank.data
        usr.city = form.city.data
        usr.about = form.about.data
        usr.password = hash_txt(form.password.data) if form.password.data else usr.password
        usr.cate = form.cate.data or 'user'
        new_role_ids = [form.role.data]  # Assuming the form data provides a list of role IDs
        new_roles = Role.query.filter(Role.id.in_(new_role_ids) ).all()
        usr.role = new_roles
            
        social_handles = \
            {'facebook': form.facebook.data, 'twitter' : form.twitter.data, 'instagram' :form.instagram.data, 'linkedin' :form.linkedin.data}
        #usr.socials = str(social_handles)
        usr.socials = social_handles

        db.session.commit()
        db.session.flush()
        flash('Your Account Has Been Updated!', 'success')
        return jsonify({ 
            'response': f'Success..!!, You"ve Updated This Account </b>..',
            'flash':'alert-success',
            'link': f''})
    
    elif request.method == 'GET':
        if handles:
            form.twitter.data = handles['twitter'] 
            form.facebook.data = handles['facebook'] 
            form.instagram.data = handles['instagram'] 
            form.linkedin.data = handles['linkedin'] 
        #form.socials.data = usr.socials
        form.photo.data = usr.photo or '0.svg'
        form.name.data = usr.name
        form.username.data = usr.username
        form.email.data = usr.email
        form.phone.data = usr.phone
        form.gender.data = usr.gender
        form.acct_no.data = usr.acct_no
        form.city.data = usr.city
        form.about.data = usr.about
        form.bank.data = usr.bank

    if request.method == "POST" and not form.validate_on_submit():
    #if not form.validate_on_submit():
        return jsonify({ 
            'response': f'invalid .. { form.errors}  </b>..',
            'flash':'alert-warning',
            'link': f''})
    context = {
                'form' : form,
                'user': usr,
                'brand': Brand.query.first(),
            }
    return render_template('auth/update.html',  **context)
    
@auth.route("/forgot", methods=['GET', 'POST'])
@db_session_management
def forgot():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ForgotForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        notifyer.reset_email(user) if user else flash('Undefined User.', 'info')
        #email.reset_email(user) if user else flash('Undefined User.', 'info')
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.signin'))
    elif request.method == 'GET':
        form.email.data = request.args.get('e')
    return render_template('auth/forgot.html', form=form)

#->for unverified-users, notice use of 'POST' instead of 'post' before it works
@auth.route("/unverified", methods=['post', 'get'])
@login_required
@db_session_management
def unverified():
    if request.method == 'POST':
        notifyer.verify_email(current_user)
        flash('Verication Emails Sent Again, Check You Mail Box', 'info')
    return render_template('auth/unverified.html')

@auth.route('/confirm/<token>', methods=['GET', 'POST'])
def confirm(token): 
    hash = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzB9.uGkjnjdwvRCetuu_kpKDTTtnYlfr6v8Lx0KtPXvowe0'
    print(f"url-hash-unveiled-> {hash_auth.unhash_it(hash)}")
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    #user = User.verify_reset_password_token(token)
    user = User.user_exists(hash_auth.unhash_it(token))
    if not user:
        return redirect(url_for('main.index'))
    
    if  user.verified == False:
        user.verified = True
        db.session.commit()
        flash(f'Weldone {user.username}, Your Email Address is Confirmed, Continue Here', 'success')
    return redirect(url_for('auth.signin', _external=True))


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token): 
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.user_exists(hash_auth.unhash_it(token))
    if not user:
        return redirect(url_for('main.index'))
    form =  ResetForm() 
    if form.validate_on_submit():
        #user.set_password(form.password.data)
        user.password = hash_txt(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.signin'))
    return render_template('auth/reset.html', form=form)


    