from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.models import User
from app import db, login_manager

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




@auth_bp.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        nickname = data.get('nickname')
        password = data.get('password')
    else:
        email = request.form.get('email')
        nickname = request.form.get('nickname')
        password = request.form.get('password')
    if not email or not nickname or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    if User.query.filter((User.email == email) | (User.nickname == nickname)).first():
        return jsonify({'error': 'Email or nickname already exists'}), 400
    user = User(
        email=email,
        nickname=nickname,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()
    # If the request is from a form, redirect to login page with a message
    if not request.is_json:
        from flask import flash, redirect, url_for
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('frontend.login_page'))
    return jsonify({'message': 'User registered successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        if not request.is_json:
            from flask import redirect, url_for
            return redirect(url_for('frontend.wishlist_page'))
        return jsonify({'message': 'Logged in successfully'})
    if not request.is_json:
        from flask import flash, redirect, url_for
        flash('Invalid credentials', 'error')
        return redirect(url_for('frontend.login_page'))
    return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    from flask import flash, redirect, url_for
    flash('You have been logged out.', 'success')
    return redirect(url_for('frontend.home'))


@auth_bp.route('/profile', methods=['GET', 'PUT', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        return jsonify({
            'email': current_user.email,
            'nickname': current_user.nickname,
            'name': current_user.name,
            'surname': current_user.surname,
            'avatar': current_user.avatar
        })
    if request.method == 'PUT':
        data = request.get_json()
        current_user.nickname = data.get('nickname', current_user.nickname)
        current_user.name = data.get('name', current_user.name)
        current_user.surname = data.get('surname', current_user.surname)
        current_user.avatar = data.get('avatar', current_user.avatar)
        db.session.commit()
        return jsonify({'message': 'Profile updated'})
    if request.method == 'POST':
        # Handle form submission for profile update
        import re
        from flask import flash, redirect, url_for
        nickname = request.form.get('nickname', current_user.nickname)
        name = request.form.get('name', current_user.name)
        surname = request.form.get('surname', current_user.surname)
        # Validate nickname: only allow letters, numbers, -, _
        if not re.match(r'^[A-Za-z0-9_-]+$', nickname):
            flash('Nickname can only contain letters, numbers, hyphens, and underscores.', 'error')
            return redirect(url_for('frontend.profile_page'))
        # Check for duplicate nickname
        from app.models.models import User
        existing = User.query.filter(User.nickname == nickname, User.id != current_user.id).first()
        if existing:
            flash('This nickname is already taken. Please choose another.', 'error')
            return redirect(url_for('frontend.profile_page'))
        current_user.nickname = nickname
        current_user.name = name
        current_user.surname = surname
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('frontend.profile_page'))
