from flask import Blueprint, request, jsonify, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user

from app import db
from app.models.models import Event, EventParticipant, User, EVENT_PARTICIPANT_STATUS_PENDING, EVENT_PARTICIPANT_STATUS_ACCEPTED, ALLOWED_CURRENCIES

events_bp = Blueprint('events', __name__, url_prefix='/events')


# -------------------------- Helper functions -------------------------------

def _user_is_event_admin(event: Event) -> bool:
    return event.admin_user_id == current_user.id


def _load_event_or_404(event_id: int) -> Event:
    event = Event.query.get_or_404(event_id)
    # Ensure current user is participant (accepted or pending if admin checking invitation) unless admin
    part = EventParticipant.query.filter_by(event_id=event.id, user_id=current_user.id).first()
    if not part and not _user_is_event_admin(event):
        abort(403)
    return event


# -------------------------- Dashboard -------------------------------------
@events_bp.route('/dashboard')
@login_required
def dashboard():
    # Accepted events
    accepted_participations = EventParticipant.query.filter_by(user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_ACCEPTED).all()
    events = [p.event for p in accepted_participations]
    # Pending invitations
    pending_participations = EventParticipant.query.filter_by(user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_PENDING).all()
    pending_events = [p.event for p in pending_participations]
    return render_template('dashboard.html', events=events, pending_events=pending_events)


# -------------------------- Create Event ----------------------------------
@events_bp.route('/create', methods=['POST'])
@login_required
def create_event():
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        date_str = data.get('date')  # Expect YYYY-MM-DD
        budget_amount = data.get('budget_amount')
        budget_currency = (data.get('budget_currency') or 'PLN').upper()
    else:
        name = request.form.get('name')
        date_str = request.form.get('date')
        budget_amount = request.form.get('budget_amount')
        budget_currency = (request.form.get('budget_currency') or 'PLN').upper()

    if not name:
        flash('Event name is required', 'error')
        return redirect(url_for('events.dashboard'))

    if budget_currency not in ALLOWED_CURRENCIES:
        flash('Unsupported currency', 'error')
        return redirect(url_for('events.dashboard'))

    from datetime import datetime as _dt
    event_date = None
    if date_str:
        try:
            event_date = _dt.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format (expected YYYY-MM-DD)', 'error')
            return redirect(url_for('events.dashboard'))

    try:
        budget_amount_val = float(budget_amount) if budget_amount else None
    except ValueError:
        flash('Budget must be a number', 'error')
        return redirect(url_for('events.dashboard'))

    event = Event()
    event.name = name
    event.date = event_date
    event.budget_amount = budget_amount_val
    event.budget_currency = budget_currency
    event.admin_user_id = current_user.id
    db.session.add(event)
    db.session.flush()  # get id
    # Add creator as accepted admin participant
    participant = EventParticipant()
    participant.event_id = event.id
    participant.user_id = current_user.id
    participant.is_admin = True
    participant.status = EVENT_PARTICIPANT_STATUS_ACCEPTED
    db.session.add(participant)
    db.session.commit()
    flash('Event created', 'success')
    return redirect(url_for('events.view_event', event_id=event.id))


# -------------------------- View Event ------------------------------------
@events_bp.route('/<int:event_id>')
@login_required
def view_event(event_id: int):
    event = _load_event_or_404(event_id)
    participants = EventParticipant.query.filter_by(event_id=event.id).all()
    return render_template('event.html', event=event, participants=participants)


# -------------------------- Edit Event ------------------------------------
@events_bp.route('/<int:event_id>/edit', methods=['POST'])
@login_required
def edit_event(event_id: int):
    event = _load_event_or_404(event_id)
    if not _user_is_event_admin(event):
        abort(403)
    name = request.form.get('name', event.name)
    date_str = request.form.get('date')
    budget_amount = request.form.get('budget_amount')
    budget_currency = (request.form.get('budget_currency') or event.budget_currency).upper()
    from datetime import datetime as _dt
    if date_str:
        try:
            event.date = _dt.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('events.view_event', event_id=event.id))
    event.name = name
    if budget_amount:
        try:
            event.budget_amount = float(budget_amount)
        except ValueError:
            flash('Budget must be numeric', 'error')
            return redirect(url_for('events.view_event', event_id=event.id))
    if budget_currency in ALLOWED_CURRENCIES:
        event.budget_currency = budget_currency
    db.session.commit()
    flash('Event updated', 'success')
    return redirect(url_for('events.view_event', event_id=event.id))


# -------------------------- Delete Event ----------------------------------
@events_bp.route('/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id: int):
    event = _load_event_or_404(event_id)
    if not _user_is_event_admin(event):
        abort(403)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted', 'success')
    return redirect(url_for('events.dashboard'))


# -------------------------- Leave Event -----------------------------------
@events_bp.route('/<int:event_id>/leave', methods=['POST'])
@login_required
def leave_event(event_id: int):
    event = _load_event_or_404(event_id)
    participant = EventParticipant.query.filter_by(event_id=event.id, user_id=current_user.id).first_or_404()
    if participant.is_admin:
        flash('Admin cannot leave. Delete the event instead.', 'error')
        return redirect(url_for('events.view_event', event_id=event.id))
    db.session.delete(participant)
    db.session.commit()
    flash('You left the event', 'success')
    return redirect(url_for('events.dashboard'))


# -------------------------- Invite User -----------------------------------
@events_bp.route('/<int:event_id>/invite', methods=['POST'])
@login_required
def invite_user(event_id: int):
    event = _load_event_or_404(event_id)
    # Any accepted participant or admin can invite
    inviter_part = EventParticipant.query.filter_by(event_id=event.id, user_id=current_user.id).first()
    if not inviter_part or inviter_part.status != EVENT_PARTICIPANT_STATUS_ACCEPTED:
        abort(403)
    # Accept both JSON and form
    if request.is_json:
        data = request.get_json()
        target_nickname = data.get('nickname')
    else:
        target_nickname = request.form.get('nickname')
    if not target_nickname:
        flash('Nickname required to invite', 'error')
        return redirect(url_for('events.view_event', event_id=event.id))
    user = User.query.filter_by(nickname=target_nickname).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('events.view_event', event_id=event.id))
    existing = EventParticipant.query.filter_by(event_id=event.id, user_id=user.id).first()
    if existing:
        flash('User already invited or participating', 'error')
        return redirect(url_for('events.view_event', event_id=event.id))
    participant = EventParticipant()
    participant.event_id = event.id
    participant.user_id = user.id
    participant.status = EVENT_PARTICIPANT_STATUS_PENDING
    participant.is_admin = False
    db.session.add(participant)
    db.session.commit()
    flash('Invitation sent', 'success')
    return redirect(url_for('events.view_event', event_id=event.id))


# -------------------------- Accept Invitation ------------------------------
@events_bp.route('/<int:event_id>/accept', methods=['POST'])
@login_required
def accept_invitation(event_id: int):
    participant = EventParticipant.query.filter_by(event_id=event_id, user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_PENDING).first_or_404()
    participant.status = EVENT_PARTICIPANT_STATUS_ACCEPTED
    db.session.commit()
    flash('Invitation accepted', 'success')
    return redirect(url_for('events.view_event', event_id=event_id))


# -------------------------- Reject Invitation ------------------------------
@events_bp.route('/<int:event_id>/reject', methods=['POST'])
@login_required
def reject_invitation(event_id: int):
    participant = EventParticipant.query.filter_by(event_id=event_id, user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_PENDING).first_or_404()
    db.session.delete(participant)
    db.session.commit()
    flash('Invitation rejected', 'success')
    return redirect(url_for('events.dashboard'))


# -------------------------- Participant wishlist ---------------------------
@events_bp.route('/<int:event_id>/participant/<int:user_id>/wishlist')
@login_required
def participant_wishlist(event_id: int, user_id: int):
    # Ensure current user is accepted participant
    me_part = EventParticipant.query.filter_by(event_id=event_id, user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_ACCEPTED).first()
    if not me_part:
        abort(403)
    target_part = EventParticipant.query.filter_by(event_id=event_id, user_id=user_id).first_or_404()
    if target_part.status != EVENT_PARTICIPANT_STATUS_ACCEPTED:
        # Allow viewing only accepted participants
        abort(403)
    from app.models.models import WishlistItem
    items = WishlistItem.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'details': item.details,
            'event': item.event,
            'link': item.link
        } for item in items
    ])


# -------------------------- API: list my events ---------------------------
@events_bp.route('/mine')
@login_required
def my_events_json():
    parts = EventParticipant.query.filter_by(user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_ACCEPTED).all()
    return jsonify([{'id': p.event.id, 'name': p.event.name} for p in parts])
