from flask import Blueprint, request, jsonify, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from datetime import datetime

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
    accepted_participations = EventParticipant.query.filter_by(user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_ACCEPTED).all()
    events = [p.event for p in accepted_participations]
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
        date_str = data.get('date')
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
    db.session.flush()
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
    if getattr(event, 'drawing_enabled', False):
        flash('Cannot invite new participants after drawing has been enabled.', 'error')
        return redirect(url_for('events.view_event', event_id=event.id))
    inviter_part = EventParticipant.query.filter_by(event_id=event.id, user_id=current_user.id).first()
    if not inviter_part or inviter_part.status != EVENT_PARTICIPANT_STATUS_ACCEPTED:
        abort(403)
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
    me_part = EventParticipant.query.filter_by(event_id=event_id, user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_ACCEPTED).first()
    if not me_part:
        abort(403)
    target_part = EventParticipant.query.filter_by(event_id=event_id, user_id=user_id).first_or_404()
    if target_part.status != EVENT_PARTICIPANT_STATUS_ACCEPTED:
        abort(403)
    from app.models.models import WishlistItem, Event as EventModel
    event = EventModel.query.get_or_404(event_id)
    items = WishlistItem.query.filter_by(user_id=user_id, currency=event.budget_currency).all()
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


# -------------------------- Drawing: enable --------------------------------
@events_bp.route('/<int:event_id>/drawing/enable', methods=['POST'])
@login_required
def enable_drawing(event_id: int):
    event = _load_event_or_404(event_id)
    if not _user_is_event_admin(event):
        abort(403)
    accepted = [p for p in EventParticipant.query.filter_by(event_id=event.id, status=EVENT_PARTICIPANT_STATUS_ACCEPTED).all()]
    if len(accepted) < 2:
        flash('Need at least 2 accepted participants to enable drawing.', 'error')
        return redirect(url_for('events.view_event', event_id=event.id))
    if event.drawing_enabled:
        flash('Drawing already enabled.', 'error')
        return redirect(url_for('events.view_event', event_id=event.id))
    import random
    user_ids = [p.user_id for p in accepted]
    for _ in range(50):
        perm = user_ids[:]
        random.shuffle(perm)
        if all(uid != perm[i] for i, uid in enumerate(user_ids)):
            break
    else:
        flash('Failed to generate drawing assignments, please retry.', 'error')
        return redirect(url_for('events.view_event', event_id=event.id))
    assignment_map = {user_ids[i]: perm[i] for i in range(len(user_ids))}
    for p in accepted:
        p.assigned_recipient_user_id = assignment_map[p.user_id]
        p.drawn_at = None
    event.drawing_enabled = True
    db.session.commit()
    flash('Drawing enabled. Participants can now draw their recipient.', 'success')
    return redirect(url_for('events.view_event', event_id=event.id))


# -------------------------- Drawing: draw my recipient ---------------------
@events_bp.route('/<int:event_id>/drawing/draw', methods=['POST'])
@login_required
def draw_recipient(event_id: int):
    event = _load_event_or_404(event_id)
    if not event.drawing_enabled:
        abort(403)
    participant = EventParticipant.query.filter_by(event_id=event.id, user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_ACCEPTED).first_or_404()
    if participant.drawn_at is not None:
        return jsonify({'error': 'Already drawn', 'recipient_nickname': participant.recipient.nickname if participant.recipient else None}), 400
    if participant.assigned_recipient_user_id is None:
        return jsonify({'error': 'No assignment found'}), 400
    participant.drawn_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'recipient_user_id': participant.assigned_recipient_user_id, 'recipient_nickname': participant.recipient.nickname})


# -------------------------- Drawing: reset ---------------------------------
@events_bp.route('/<int:event_id>/drawing/reset', methods=['POST'])
@login_required
def reset_drawing(event_id: int):
    event = _load_event_or_404(event_id)
    if not _user_is_event_admin(event):
        abort(403)
    participants = EventParticipant.query.filter_by(event_id=event.id).all()
    for p in participants:
        p.assigned_recipient_user_id = None
        p.drawn_at = None
    event.drawing_enabled = False
    db.session.commit()
    flash('Drawing has been reset.', 'success')
    return redirect(url_for('events.view_event', event_id=event.id))


# -------------------------- API: list my events ---------------------------
@events_bp.route('/mine')
@login_required
def my_events_json():
    parts = EventParticipant.query.filter_by(user_id=current_user.id, status=EVENT_PARTICIPANT_STATUS_ACCEPTED).all()
    return jsonify([{'id': p.event.id, 'name': p.event.name} for p in parts])
