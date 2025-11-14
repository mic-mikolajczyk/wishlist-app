from datetime import datetime
from datetime import timezone

from flask_login import UserMixin

from app import db

# ---------------------------------------------------------------------------
# Event & Participation layer
# ---------------------------------------------------------------------------
# We introduce a grouping layer around wishlists: Events. Each Event has
# participants and one admin (the creator). Invitations are modeled as
# EventParticipant rows with status='pending'.
# Status lifecycle: pending -> accepted OR rejected (row can optionally be kept).
# For simplicity we delete the row on rejection, but keep constant for clarity.

EVENT_PARTICIPANT_STATUS_PENDING = 'pending'
EVENT_PARTICIPANT_STATUS_ACCEPTED = 'accepted'
EVENT_PARTICIPANT_STATUS_REJECTED = 'rejected'

ALLOWED_CURRENCIES = {'PLN', 'EUR', 'USD'}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nickname = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64))
    surname = db.Column(db.String(64))
    avatar = db.Column(db.String(256), default='default_avatar.png')
    password_hash = db.Column(db.String(128), nullable=False)
    wishlist_items = db.relationship('WishlistItem', backref='owner', lazy=True)
    # Specify foreign_keys to disambiguate from assigned_recipient_user_id
    event_participations = db.relationship(
        'EventParticipant', backref='user', lazy=True,
        cascade='all, delete-orphan', foreign_keys='EventParticipant.user_id'
    )

    @property
    def events(self):
        """Return events where user participation status is accepted.
        Using a defensive getattr to satisfy static analysis tools.
        """
        participations = getattr(self, 'event_participations', [])
        return [ep.event for ep in participations if ep.status == EVENT_PARTICIPANT_STATUS_ACCEPTED]

    def __repr__(self):
        return f'<User {self.email}>'


class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float)
    currency = db.Column(db.String(3), default='PLN')  # NEW: currency for price consistency
    details = db.Column(db.Text)
    event = db.Column(db.String(128))
    link = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<WishlistItem {self.name} {self.price or ''} {self.currency}>"


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    # Map to existing legacy column names already present in DB
    date = db.Column('event_date', db.Date)  # existing column event_date
    budget_amount = db.Column('budget', db.Float)  # existing column budget
    budget_currency = db.Column('currency', db.String(3), default='PLN')  # existing column currency
    admin_user_id = db.Column('admin_id', db.Integer, db.ForeignKey('user.id'), nullable=False)  # existing column admin_id
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # new column via migration
    # Drawing feature flag - when enabled admin generated assignments
    drawing_enabled = db.Column(db.Boolean, default=False, nullable=False)
    # Archived flag: when true the event is read-only (no edits, invites, drawing actions)
    archived = db.Column(db.Boolean, default=False, nullable=False)
    # Active flag retained for backward compatibility with older schema expecting NOT NULL is_active
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    admin = db.relationship('User', foreign_keys=[admin_user_id])
    participants = db.relationship('EventParticipant', backref='event', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Event {self.name} ({self.budget_amount} {self.budget_currency})>'

    def add_participant(self, user, is_admin=False, status=EVENT_PARTICIPANT_STATUS_PENDING):
        existing = EventParticipant.query.filter_by(event_id=self.id, user_id=user.id).first()
        if existing:
            return existing
        # Construct manually to satisfy static analysis.
        participant = EventParticipant()
        participant.event_id = self.id
        participant.user_id = user.id
        participant.is_admin = is_admin
        participant.status = status
        db.session.add(participant)
        return participant

    def accepted_participants(self):
        participants = getattr(self, 'participants', [])
        return [p for p in participants if p.status == EVENT_PARTICIPANT_STATUS_ACCEPTED]


class EventParticipant(db.Model):
    __tablename__ = 'event_participant'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(16), default=EVENT_PARTICIPANT_STATUS_PENDING, nullable=False)
    invited_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    accepted_at = db.Column(db.DateTime)
    # Pre-assigned recipient user id (secret until user draws)
    assigned_recipient_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    drawn_at = db.Column(db.DateTime)  # timestamp when user revealed recipient
    recipient = db.relationship('User', foreign_keys=[assigned_recipient_user_id], lazy=True)

    __table_args__ = (
        db.UniqueConstraint('event_id', 'user_id', name='uq_event_user'),
    )

    def accept(self):
        self.status = EVENT_PARTICIPANT_STATUS_ACCEPTED
        self.accepted_at = datetime.now(timezone.utc)

    def reject(self):
        self.status = EVENT_PARTICIPANT_STATUS_REJECTED

    def __repr__(self):
        return f'<EventParticipant user={self.user_id} event={self.event_id} status={self.status} recipient={self.assigned_recipient_user_id} drawn={bool(self.drawn_at)}>'
