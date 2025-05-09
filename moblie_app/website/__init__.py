from flask import Flask
from .database import db  # Import db from the new file
from flask_login import LoginManager
from .models import User, Buyer, Seller  # This import will now work
import os
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key
csrf = CSRFProtect(app)
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__ , static_folder='static')
    app.config['UPLOAD_FOLDER'] = 'static/'
    app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a strong secret
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_PROTECTION'] = 'strong'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True  # Ensure you're using HTTPS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    db.init_app(app)

    # Register blueprints
    from .views import views
    from .auth import auth
    from .seller import seller
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(seller, url_prefix='/seller')
    app.register_blueprint(auth, url_prefix='/auth')

    # Create database tables
    with app.app_context():
        db.create_all()  # Creates the tables

    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # First, try to find the user as a Buyer
        return User.query.get(int(user_id))

    return app