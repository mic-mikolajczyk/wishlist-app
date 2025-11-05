from flask import Blueprint
from flask import jsonify
from flask import request

from app.models.models import User
from app.models.models import WishlistItem

public_bp = Blueprint('public', __name__, url_prefix='/public')


@public_bp.route('/users', methods=['GET'])
def search_users():
    query = request.args.get('q', '')
    users = User.query.filter(
        (User.nickname.ilike(f'%{query}%')) | (User.name.ilike(f'%{query}%')) | (User.surname.ilike(f'%{query}%'))
    ).all()
    return jsonify([
        {
            'id': user.id,
            'nickname': user.nickname,
            'avatar': user.avatar,
            'name': user.name,
            'surname': user.surname
        } for user in users
    ])


@public_bp.route('/wishlist/<int:user_id>', methods=['GET'])
def view_wishlist(user_id):
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    query = WishlistItem.query.filter_by(user_id=user_id)
    if min_price is not None:
        query = query.filter(WishlistItem.price >= min_price)
    if max_price is not None:
        query = query.filter(WishlistItem.price <= max_price)
    items = query.all()
    return jsonify([
        {
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'currency': item.currency,
            'details': item.details,
            'event': item.event,
            'link': item.link
        } for item in items
    ])
