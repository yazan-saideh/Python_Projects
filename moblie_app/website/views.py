from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Estate
from . import db
import json

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    # Check if the user is a buyer or seller
    if current_user.account_type == 'buyer':
        return redirect(url_for('views.buyer_home'))  # Redirect to buyer home page
    elif current_user.account_type == 'seller':
        return redirect(url_for('seller.seller_home'))  # Redirect to seller home page


@views.route('/buyer')
@login_required
def buyer_home():
    # Render the buyer home page
    estates = Estate.query.all()
    return render_template("buyer.html", user=current_user, estates =estates)


