from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from website.models import Buyer, Seller, AccountType
from werkzeug.security import generate_password_hash, check_password_hash
from website import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        buyer = Buyer.query.filter_by(email=email).first()
        seller = Seller.query.filter_by(email=email).first()

        # Check if either buyer or seller was found
        user = buyer or seller

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                session['account_type'] = 'buyer' if isinstance(user,Buyer) else 'seller'  # Store account type in session
                return redirect(url_for('views.home'))

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        account_type = request.form.get('account_type')

        if account_type not in ['buyer', 'seller']:
            flash('Invalid account type.', category='error')
            return redirect(url_for('auth.sign_up'))

        # Check if the email already exists
        user = None
        if account_type == 'buyer':
            user = Buyer.query.filter_by(email=email).first()
        else:
            user = Seller.query.filter_by(email=email).first()

        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            # Create a new user based on the selected account type
            if account_type == 'buyer':
                new_user = Buyer(
                    email=email,
                    first_name=first_name,
                    password=generate_password_hash(password1),
                    account_type=AccountType.buyer  # Use the enum here
                )
            else:
                new_user = Seller(
                    email=email,
                    first_name=first_name,
                    password=generate_password_hash(password1),
                    account_type=AccountType.seller  # Use the enum here
                )

            db.session.add(new_user)
            try:
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created!', category='success')
                return redirect(url_for('views.home'))
            except Exception as e:
                db.session.rollback()  # Rollback on error
                flash('An error occurred while creating the account. Please try again.', category='error')
                print(f"Error committing user t``o database: {e}")  # Debugging line


    return render_template("signup.html", user=current_user)

# Disable caching for all requests
@auth.after_request
def add_header(response):
    # Disable caching
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response