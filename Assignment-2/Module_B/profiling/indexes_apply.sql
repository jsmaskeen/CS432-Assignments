USE cabSharing;

-- Composite indexes for SubTask 4 (API-query targeted)
-- 1) Rides listing and admin ride views (status filter + departure ordering)
CREATE INDEX idx_rides_status_departure_time ON Rides (Ride_Status, Departure_Time);

-- 2) Pending bookings for a ride (ride/status filter + booked_at ordering)
CREATE INDEX idx_bookings_ride_status_booked_at ON Bookings (RideID, Booking_Status, Booked_At);

-- 3) Rider's booking history (passenger filter + booked_at ordering)
CREATE INDEX idx_bookings_passenger_booked_at ON Bookings (Passenger_MemberID, Booked_At);

-- 4) Reviews by ride/member with created_at ordering
CREATE INDEX idx_reviews_ride_created_at ON Reputation_Reviews (RideID, Created_At);
CREATE INDEX idx_reviews_reviewer_created_at ON Reputation_Reviews (Reviewer_MemberID, Created_At);
CREATE INDEX idx_reviews_reviewee_created_at ON Reputation_Reviews (Reviewee_MemberID, Created_At);

-- 5) Settlements listing joins through bookings and rides
CREATE INDEX idx_rides_host_ride_id ON Rides (Host_MemberID, RideID);
CREATE INDEX idx_settlements_settlement_booking ON Cost_Settlements (SettlementID, BookingID);
