## Plan: Module B Remaining Tables + UI

Implement remaining schema-backed modules (Locations, Reviews, User Preferences, Cost Settlements, Ride Chat) with session-validated APIs, role-aware permissions, and frontend screens integrated into the current app. Keep locations fixed/predefined, gate reviews to completed rides, allow host/passenger settlement updates, and restrict chat to host + confirmed passengers.

**Steps**

1. Phase A - Data model completion (depends on existing auth/rides models): add SQLAlchemy ORM mappings for `Locations`, `Reputation_Reviews`, `User_Preferences`, `Cost_Settlements`, and `Ride_Chat`; add relationships/indexes matching dump constraints; include startup schema checks/migrations for any new app-specific columns only.
2. Phase A - Shared authorization and audit integration (parallel with step 1 after model names are fixed): add reusable permission helpers for participant-only ride access and role checks; ensure every data-modifying endpoint writes JSON-line audit events to `audit.log` with actor, action, status, and record identifiers.
3. Phase B - Locations API (depends on step 1): implement read-only predefined location endpoints (list/search/detail/by geohash) with auth validation; no custom creation endpoint per decision.
4. Phase B - Preferences API (depends on step 1): implement GET/POST/PUT for current user preferences with one-row-per-member behavior and default bootstrap when missing.
5. Phase C - Reviews API (depends on steps 1-2): implement participant-scoped review creation for completed rides only; enforce uniqueness and self-review prohibition; expose member review listing and reputation summary endpoint.
6. Phase C - Settlements API (depends on steps 1-2): implement settlement fetch endpoints and status update endpoint allowing host or passenger (for the related booking) to mark settled; include authorization checks and audit writes.
7. Phase C - Ride Chat API (depends on steps 1-2): implement list/send chat messages only for host + confirmed passengers; add pagination and audit for message creation.
8. Phase D - Router and schema integration (depends on steps 3-7): register all new routers, create Pydantic request/response schemas, add consistent error responses and tags in OpenAPI.
9. Phase E - Frontend API client extension (depends on step 8): expand client methods for locations/preferences/reviews/settlements/chat and normalize error messages.
10. Phase E - Frontend UI pages (depends on step 9): add Preferences, Reviews, Settlements, and Locations pages; extend rides page with chat panel for selected ride; enforce auth/role-aware rendering. Also an admin only page to see all audit logs in a readable format as well as all the members in the app for admin management.
11. Phase F - Validation and demo readiness (depends on all prior steps): test all flows manually and via endpoint checks, verify audit file entries for every mutation, confirm unauthorized attempts are blocked and visible in logs.

**Relevant files**

- `d:/College - IIT Gn/Sem 6/Databases/DBProject/SQL-Dump/dump.sql` — source constraints and reference seed behavior.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/models/location.py` — new `Locations` ORM mapping.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/models/reputation_review.py` — new reviews model with uniqueness/check constraints.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/models/user_preference.py` — new user preferences model (1:1 with member).
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/models/cost_settlement.py` — new settlement model (1:1 with booking).
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/models/ride_chat.py` — new ride chat message model.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/api/routes/locations.py` — location read/search endpoints.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/api/routes/preferences.py` — preference CRUD for current user.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/api/routes/reviews.py` — review/reputation endpoints.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/api/routes/settlements.py` — settlement retrieval/update endpoints.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/api/routes/chat.py` — ride chat list/send endpoints.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/api/dependencies.py` — participant and role authorization helpers.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/core/audit.py` — JSON-line audit logging utility.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/backend/api/router.py` — router registration.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/frontend/src/api.js` — frontend client additions.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/frontend/src/App.jsx` — route registration for new pages.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/frontend/src/pages/RidesPage.jsx` — add ride chat panel.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/frontend/src/pages/PreferencesPage.jsx` — new preferences UI.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/frontend/src/pages/ReviewsPage.jsx` — new reviews UI.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/frontend/src/pages/SettlementsPage.jsx` — new settlements UI.
- `d:/College - IIT Gn/Sem 6/Databases/DBProject/frontend/src/pages/LocationsPage.jsx` — new locations explorer UI.

**Verification**

1. Schema parity check: confirm new ORM models align with table constraints and enums from dump.
2. Auth/session enforcement check: verify 401/403 behavior for every new endpoint when unauthenticated/unauthorized.
3. Reviews rule check: verify review creation fails for non-completed rides and non-participants.
4. Settlement permission check: verify only host or passenger of the booking can update payment status.
5. Chat permission check: verify only host + confirmed passengers can read/send messages.
6. Locations policy check: verify endpoints are read-only and no custom location writes exist.
7. Audit verification: for each mutation endpoint, verify one JSON line is appended to `audit.log` with action/status/actor/details.
8. Frontend integration check: complete end-to-end flows for preferences, reviews, settlements, locations, and ride chat without console/runtime errors.

**Decisions**

- Reviews allowed only when ride status is `Completed`.
- Settlements can be marked by host or passenger tied to the booking.
- Chat access is restricted to host and confirmed passengers.
- Locations are fixed/predefined; no custom creation in this iteration.
- UI scope includes Preferences, Reviews, Settlements, Locations pages, plus chat embedded in rides page.

**Further Considerations**

1. Reputation update strategy: immediate aggregate update on each review write vs read-time calculation; recommendation is immediate update for responsive profile UI.
2. Chat realtime level: REST polling now vs WebSocket now; recommendation is REST first for assignment reliability, WebSocket later if time remains.
3. Audit coverage depth: only mutations vs include read denials; recommendation is mutations mandatory + log denied mutation attempts for stronger compliance proof.
