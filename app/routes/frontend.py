
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for
from flask_login import current_user
from flask_login import login_required

frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/users')
def user_search_page():
    return render_template('user_search.html')


@frontend_bp.route('/wishlist')
@login_required
def wishlist_page():
    return render_template('wishlist.html')


@frontend_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('events.dashboard'))
    return render_template('home.html')


@frontend_bp.route('/login')
def login_page():
    return render_template('login.html')


@frontend_bp.route('/register')
def register_page():
    return render_template('register.html')


@frontend_bp.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html', user=current_user)

 
@frontend_bp.route('/settings')
def settings_page():
    """Settings page: language selection always visible; logout shown if authenticated."""
    return render_template('settings.html')
