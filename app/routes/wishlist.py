from flask import Blueprint
from flask import jsonify
from flask import request
from flask_login import current_user
from flask_login import login_required

from app import db
from app.models.models import WishlistItem

wishlist_bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')


@wishlist_bp.route('/<int:item_id>', methods=['GET'])
@login_required
def get_item(item_id):
    item = WishlistItem.query.filter_by(
        id=item_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'id': item.id,
        'name': item.name,
        'price': item.price,
        'details': item.details,
        'event': item.event,
        'link': item.link
    })


@wishlist_bp.route('/', methods=['GET'])
@login_required
def get_wishlist():
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'price': item.price,
        'details': item.details,
        'event': item.event,
        'link': item.link
    } for item in items])


@wishlist_bp.route('/', methods=['POST'])
@login_required
def add_item():
    data = request.get_json()
    item = WishlistItem(
        name=data.get('name'),
        price=data.get('price'),
        details=data.get('details'),
        event=data.get('event'),
        link=data.get('link'),
        user_id=current_user.id
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'message': 'Item added', 'id': item.id}), 201


@wishlist_bp.route('/<int:item_id>', methods=['PUT'])
@login_required
def edit_item(item_id):
    item = WishlistItem.query.filter_by(
        id=item_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    item.name = data.get('name', item.name)
    item.price = data.get('price', item.price)
    item.details = data.get('details', item.details)
    item.event = data.get('event', item.event)
    item.link = data.get('link', item.link)
    # Picture field removed
    db.session.commit()
    return jsonify({'message': 'Item updated'})


@wishlist_bp.route('/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    item = WishlistItem.query.filter_by(
        id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted'})
