# Wishlist App with Events Layer

This application provides a wishlist management system for users and now introduces an **Events** grouping layer. Users can create events, invite other users, and view each participant's wishlist in the context of an event.

## New Features

- Events Dashboard after login listing:
  - Accepted events (you participate in)
  - Pending invitations (accept / reject)
- Event creation with: name, (optional) date, budget amount + currency (`PLN`, `EUR`, `USD`).
- Event admin (creator) can edit or delete the event.
- Participants can leave an event (admins must delete instead of leaving).
- Invitation flow: any accepted participant may invite another user by nickname; invited users must accept or reject.
- Participant list shows status badges: `Admin`, `Pending`.
- Clicking an accepted participant loads their wishlist (read-only in this context).
- Embedded "My Wishlist" section under participant list with full-width Add button and in-place edit/delete actions.

### Internationalization (i18n)

Polish language support has been added and is now the default locale.

Key points:

- Uses `Flask-Babel` for translations.
- Default locale: `pl` (see `Config.BABEL_DEFAULT_LOCALE`).
- Language switch route: `/lang/<locale>` (currently supports `pl` and `en`).
- Templates wrap translatable strings with `{{ _('Text') }}`.
- Polish catalog: `app/translations/pl/LC_MESSAGES/messages.po` (compiled to `.mo`).

To add or update translations:

```bash
pybabel extract -F babel.cfg -o messages.pot .        # (create babel.cfg first if expanding extraction)
pybabel update -i messages.pot -d app/translations    # updates existing catalogs
# OR initialize a new language (example for German):
pybabel init -i messages.pot -d app/translations -l de
pybabel compile -d app/translations
```

Minimal manual workflow (if not using automated extraction): edit the relevant `messages.po` and re-run:

```bash
pybabel compile -d app/translations
```

If you add user-specific language preferences later, store the chosen locale (e.g. in the `User` model) and adjust the `get_locale()` function in `app/__init__.py` to read it.

## Data Model Additions

Two new tables:

- `event`: Stores core event metadata.
- `event_participant`: Links users to events with fields: `is_admin`, `status` (`pending`, `accepted`).


See `app/models/models.py` for implementation.


## Migrations

Run Alembic migration to create new tables:

```bash
flask db upgrade
```

(If using direct Alembic invoke: `alembic upgrade head`).

## Key Endpoints (Blueprint: `/events`)

- `GET /events/dashboard` – Dashboard view.
- `POST /events/create` – Create an event.
- `GET /events/<event_id>` – Event page.
- `POST /events/<event_id>/edit` – Edit (admin only).
- `POST /events/<event_id>/delete` – Delete event (admin only).
- `POST /events/<event_id>/leave` – Leave (non-admin).
- `POST /events/<event_id>/invite` – Invite user by nickname.
- `POST /events/<event_id>/accept` – Accept invitation.
- `POST /events/<event_id>/reject` – Reject invitation.
- `GET /events/<event_id>/participant/<user_id>/wishlist` – JSON wishlist of participant (accepted only).

## UI Templates

- `dashboard.html` – Event & invitations overview.
- `event.html` – Event detail + participants + participant wishlist + embedded personal wishlist.

## Navigation Changes

The top and mobile navigation include an **Events** link which is now the primary landing page after login.

## Notes & Next Steps

Potential future enhancements:

- Add role transfer (admin reassignment) when original admin leaves.
- Add server-side pagination for large participant or wishlist lists.
- Add real-time updates (WebSocket) for invitations status.
- Currency formatting helpers per locale.

## Development

To run locally (after creating & activating a virtual environment):

```bash
pip install -r requirements.txt
flask db upgrade
flask run
```

## License

(Define application license here.)
