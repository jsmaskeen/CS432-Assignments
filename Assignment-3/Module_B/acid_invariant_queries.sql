-- Q1: duplicate bookings for same ride/passenger (must be 0 rows)
SELECT RideID, Passenger_MemberID, COUNT(*) AS cnt
FROM Bookings
GROUP BY RideID, Passenger_MemberID
HAVING COUNT(*) > 1;

-- Q2: duplicate participants for same ride/member (must be 0 rows)
SELECT RideID, MemberID, COUNT(*) AS cnt
FROM Ride_Participants
GROUP BY RideID, MemberID
HAVING COUNT(*) > 1;

-- Q3: duplicate settlements for same booking (must be 0 rows)
SELECT BookingID, COUNT(*) AS cnt
FROM Cost_Settlements
GROUP BY BookingID
HAVING COUNT(*) > 1;

-- Q4: seat mismatch against confirmed non-host bookings (must be 0 rows)
SELECT
    r.RideID,
    r.Max_Capacity,
    r.Available_Seats,
    COALESCE(c.confirmed_non_host_count, 0) AS confirmed_non_host_count,
    (r.Max_Capacity - 1 - COALESCE(c.confirmed_non_host_count, 0)) AS expected_available
FROM Rides r
LEFT JOIN (
    SELECT b.RideID, COUNT(*) AS confirmed_non_host_count
    FROM Bookings b
    JOIN Rides rr ON rr.RideID = b.RideID
    WHERE b.Booking_Status = 'Confirmed'
      AND b.Passenger_MemberID <> rr.Host_MemberID
    GROUP BY b.RideID
) c ON c.RideID = r.RideID
WHERE r.Available_Seats <> (r.Max_Capacity - 1 - COALESCE(c.confirmed_non_host_count, 0));

-- Q5: invalid seat bounds (must be 0 rows)
SELECT RideID, Max_Capacity, Available_Seats
FROM Rides
WHERE Available_Seats < 0 OR Available_Seats > Max_Capacity;

-- Q6: invalid ride status vs seats for active rides (must be 0 rows)
SELECT RideID, Ride_Status, Available_Seats
FROM Rides
WHERE (Ride_Status = 'Full' AND Available_Seats <> 0)
   OR (Ride_Status = 'Open' AND Available_Seats = 0);

-- Q7: host must have exactly one confirmed host booking per ride (must be 0 rows)
SELECT r.RideID, r.Host_MemberID, COUNT(b.BookingID) AS host_confirmed_rows
FROM Rides r
LEFT JOIN Bookings b
  ON b.RideID = r.RideID
 AND b.Passenger_MemberID = r.Host_MemberID
 AND b.Booking_Status = 'Confirmed'
GROUP BY r.RideID, r.Host_MemberID
HAVING host_confirmed_rows <> 1;

-- Q8: host must exist in ride participants as Host role (must be 0 rows)
SELECT r.RideID, r.Host_MemberID
FROM Rides r
LEFT JOIN Ride_Participants rp
  ON rp.RideID = r.RideID
 AND rp.MemberID = r.Host_MemberID
 AND rp.Role = 'Host'
WHERE rp.ParticipantID IS NULL;

-- Q9: confirmed passenger must have participant row (must be 0 rows)
SELECT b.BookingID, b.RideID, b.Passenger_MemberID
FROM Bookings b
LEFT JOIN Ride_Participants rp
  ON rp.RideID = b.RideID
 AND rp.MemberID = b.Passenger_MemberID
 AND rp.Role IN ('Passenger', 'Host')
WHERE b.Booking_Status = 'Confirmed'
  AND rp.ParticipantID IS NULL;

-- Q10: completed rides must have settlement for each confirmed non-host booking (must be 0 rows)
SELECT b.BookingID, b.RideID
FROM Bookings b
JOIN Rides r ON r.RideID = b.RideID
LEFT JOIN Cost_Settlements s ON s.BookingID = b.BookingID
WHERE r.Ride_Status = 'Completed'
  AND b.Booking_Status = 'Confirmed'
  AND b.Passenger_MemberID <> r.Host_MemberID
  AND s.SettlementID IS NULL;

-- Q11: settlement without confirmed booking (must be 0 rows)
SELECT s.SettlementID, s.BookingID
FROM Cost_Settlements s
LEFT JOIN Bookings b ON b.BookingID = s.BookingID
WHERE b.BookingID IS NULL
   OR b.Booking_Status <> 'Confirmed';
