# App Methodology, Functionality, and Approach

This application is a campus ride-sharing system built with a map-first workflow. The core idea is that every ride and booking is represented by start/end geohashes, so both discovery and matching stay location-consistent across the platform. The system is split into a React frontend for user interaction and a MySQL + FastAPI + SqlAlchemy backend for business rules, authorization, persistence, and auditing.

## Methodology and System Approach

The implementation follows a state-driven ride lifecycle:

1. A host publishes a ride (Open/Full based on available seats).
2. Riders submit booking requests (initially Pending).
3. Host accepts/rejects requests.
4. Ride transitions to Started and then Completed.
5. Settlements are generated and payment status can be updated.

For correctness and security, the backend remains the source of truth for validations (seat checks, role checks, status checks, duplicate booking checks, and settlement authorization). The frontend provides convenience features like map previews and suggestion search, but all critical checks are enforced server-side.

The project also uses layered observability:

1. Application-level JSON audit logs for API actions.
2. Database-trigger logs that classify row changes as API-authorized vs direct DB modifications (unauthorized), exposed to admins in the UI.

## Frontend Functionality (Page-wise)

1. **Home**  
   Presents the platform concept and directs users to ride booking/hosting flow.

2. **Login/Register**  
   Supports account creation and login, stores JWT token client-side, and refreshes session state in the app shell. Role information is shown after authentication.

3. **Rides (Main Booking + Hosting Page)**  
   Combines two modes:
    - **Booking mode**: browse available rides, select a ride, choose pickup/drop through typed suggestions or map clicks, preview route distance, and submit booking.
    - **Hosting mode**: choose ride start/end via suggestions/map, set departure/vehicle/capacity/fare, preview host route distance, and publish ride.

    The map visualizes:
    - available ride lines,
    - selected ride focus,
    - booking pickup/drop markers and route,
    - host draft route,
    - selected ride route including confirmed stops.

4. **My Bookings**  
   Shows user bookings with status and distance. Provides:
    - delete booking,
    - quick access to manage ride (if user is the host),
    - chat access (confirmed bookings/host),
    - review prompt for completed rides (review participants flow).

5. **Manage Ride (Host Control Panel)**  
   Host can:
    - edit vehicle type, capacity, and filled seats,
    - start/end ride,
    - review confirmed bookings,
    - inspect pending requests with route preview (old vs new route overlays),
    - accept/reject pending requests,
    - view settlement status per confirmed booking (settled/unpaid/not generated) and refresh settlements.

6. **Ride Chat**  
   Real-time WebSocket chat for host and confirmed passengers, with history loading and live message broadcasting.

7. **Locations**  
   Search and list known locations, and create new locations with:
    - location name/type,
    - geohash from map click or suggestion,
    - suggestion assistance from existing locations plus geocoding search.

8. **Saved Locations**  
   User-specific saved addresses (label + selected location), with create and delete operations for quick reuse.

9. **Profile**  
   Displays current user identity, role, and account info, with quick navigation to preferences, reviews, and settlements.

10. **Preferences**  
    Stores user ride preferences (gender preference, notification preference flag, music preference).

11. **Reviews**  
    Displays both:
    - reviews received by the current member,
    - reviews given by the current member,
      along with visible reputation score context.

12. **Settlements**  
    Lists user-related settlements and allows payment status updates by settlement ID.

13. **Admin**  
    Central operational dashboard for admins:
    - member list and role management,
    - ride/bookings aggregate statistics,
    - open/active/completed ride lists,
    - ride inspection (details, participants, chat history),
    - API audit log viewing,
    - unauthorized direct DB modification monitoring with summary counts and detailed records.

## Key Functional Characteristics

1. **Map-first UX**: geohash-based location consistency with route previews.
2. **Host workflow completeness**: create, manage, start/end, and settlement visibility.
3. **Passenger workflow completeness**: discover, request booking, chat, review, settlement tracking.
4. **Role-based administration**: visibility, moderation, and audit supervision.
5. **Auditability**: both action logs and trigger-backed unauthorized DB change detection.

This architecture balances usability (interactive frontend, live map/chat) with strict backend enforcement and traceability, which is appropriate for a database-focused assignment requiring both functional completeness and auditable data operations.
