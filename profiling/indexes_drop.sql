USE cabSharing;

-- Rollback indexes created by indexes_apply.sql
DROP INDEX idx_settlements_settlement_booking ON Cost_Settlements;
DROP INDEX idx_rides_host_ride_id ON Rides;

DROP INDEX idx_reviews_reviewee_created_at ON Reputation_Reviews;
DROP INDEX idx_reviews_reviewer_created_at ON Reputation_Reviews;
DROP INDEX idx_reviews_ride_created_at ON Reputation_Reviews;

DROP INDEX idx_bookings_passenger_booked_at ON Bookings;
DROP INDEX idx_bookings_ride_status_booked_at ON Bookings;

DROP INDEX idx_rides_status_departure_time ON Rides;
