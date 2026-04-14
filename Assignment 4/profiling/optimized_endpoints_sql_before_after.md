# Optimized Endpoints: SQL Before vs After Indexing

These are the endpoints intentionally targeted by the plug-in index set.
The API SQL statements are the same before/after; performance changes come from index availability and query plan changes.

| Endpoint | Before Avg (ms) | After Avg (ms) | Delta (ms) | Improvement % |
|---|---:|---:|---:|---:|
| rides :: GET /api/v1/rides | 22.62 | 10.14 | 12.48 | 55.19% |
| admin :: GET /api/v1/admin/rides/open | 217.33 | 207.64 | 9.68 | 4.45% |
| admin :: GET /api/v1/admin/rides/completed | 219.39 | 209.72 | 9.67 | 4.41% |
| admin :: GET /api/v1/admin/rides/active | 18.64 | 6.03 | 12.61 | 67.63% |
| bookings :: GET /api/v1/rides/my/bookings | 8.14 | 7.66 | 0.49 | 5.98% |
| bookings :: GET /api/v1/rides/{ride_id}/bookings/pending | 8.41 | 8.27 | 0.13 | 1.60% |
| reviews :: GET /api/v1/reviews/ride/{ride_id} | 6.94 | 6.81 | 0.13 | 1.86% |
| reviews :: GET /api/v1/reviews/member/{member_id} | 8.37 | 10.99 | -2.62 | -31.23% |
| reviews :: GET /api/v1/reviews/my | 7.93 | 8.58 | -0.65 | -8.24% |
| settlements :: GET /api/v1/settlements/my | 25.07 | 26.29 | -1.21 | -4.84% |

## rides :: GET /api/v1/rides

**SQL (Before Indexing):**

```sql
SELECT * FROM Rides WHERE Ride_Status = 'Open' ORDER BY Departure_Time ASC LIMIT :limit;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Rides WHERE Ride_Status = 'Open' ORDER BY Departure_Time ASC LIMIT :limit;
```

**Relevant Indexes:**

- idx_rides_status_departure_time (Ride_Status, Departure_Time)

## admin :: GET /api/v1/admin/rides/open

**SQL (Before Indexing):**

```sql
SELECT * FROM Rides WHERE Ride_Status = 'Open' ORDER BY Departure_Time ASC;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Rides WHERE Ride_Status = 'Open' ORDER BY Departure_Time ASC;
```

**Relevant Indexes:**

- idx_rides_status_departure_time (Ride_Status, Departure_Time)

## admin :: GET /api/v1/admin/rides/completed

**SQL (Before Indexing):**

```sql
SELECT * FROM Rides WHERE Ride_Status = 'Completed' ORDER BY Departure_Time DESC;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Rides WHERE Ride_Status = 'Completed' ORDER BY Departure_Time DESC;
```

**Relevant Indexes:**

- idx_rides_status_departure_time (Ride_Status, Departure_Time)

## admin :: GET /api/v1/admin/rides/active

**SQL (Before Indexing):**

```sql
SELECT * FROM Rides WHERE Ride_Status = 'Started' ORDER BY Departure_Time ASC;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Rides WHERE Ride_Status = 'Started' ORDER BY Departure_Time ASC;
```

**Relevant Indexes:**

- idx_rides_status_departure_time (Ride_Status, Departure_Time)

## bookings :: GET /api/v1/rides/my/bookings

**SQL (Before Indexing):**

```sql
SELECT * FROM Bookings WHERE Passenger_MemberID = :member_id ORDER BY Booked_At DESC;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Bookings WHERE Passenger_MemberID = :member_id ORDER BY Booked_At DESC;
```

**Relevant Indexes:**

- idx_bookings_passenger_booked_at (Passenger_MemberID, Booked_At)

## bookings :: GET /api/v1/rides/{ride_id}/bookings/pending

**SQL (Before Indexing):**

```sql
SELECT * FROM Bookings WHERE RideID = :ride_id AND Booking_Status = 'Pending' ORDER BY Booked_At DESC;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Bookings WHERE RideID = :ride_id AND Booking_Status = 'Pending' ORDER BY Booked_At DESC;
```

**Relevant Indexes:**

- idx_bookings_ride_status_booked_at (RideID, Booking_Status, Booked_At)

## reviews :: GET /api/v1/reviews/ride/{ride_id}

**SQL (Before Indexing):**

```sql
SELECT * FROM Reputation_Reviews WHERE RideID = :ride_id ORDER BY Created_At DESC;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Reputation_Reviews WHERE RideID = :ride_id ORDER BY Created_At DESC;
```

**Relevant Indexes:**

- idx_reviews_ride_created_at (RideID, Created_At)

## reviews :: GET /api/v1/reviews/member/{member_id}

**SQL (Before Indexing):**

```sql
SELECT * FROM Reputation_Reviews WHERE Reviewer_MemberID = :member_id OR Reviewee_MemberID = :member_id ORDER BY Created_At DESC;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Reputation_Reviews WHERE Reviewer_MemberID = :member_id OR Reviewee_MemberID = :member_id ORDER BY Created_At DESC;
```

**Relevant Indexes:**

- idx_reviews_reviewer_created_at (Reviewer_MemberID, Created_At)
- idx_reviews_reviewee_created_at (Reviewee_MemberID, Created_At)

## reviews :: GET /api/v1/reviews/my

**SQL (Before Indexing):**

```sql
SELECT * FROM Reputation_Reviews WHERE Reviewer_MemberID = :member_id ORDER BY Created_At DESC;
```

**SQL (After Indexing):**

```sql
SELECT * FROM Reputation_Reviews WHERE Reviewer_MemberID = :member_id ORDER BY Created_At DESC;
```

**Relevant Indexes:**

- idx_reviews_reviewer_created_at (Reviewer_MemberID, Created_At)

## settlements :: GET /api/v1/settlements/my

**SQL (Before Indexing):**

```sql
SELECT cs.* FROM Cost_Settlements cs JOIN Bookings b ON b.BookingID = cs.BookingID JOIN Rides r ON r.RideID = b.RideID WHERE b.Passenger_MemberID = :member_id OR r.Host_MemberID = :member_id ORDER BY cs.SettlementID DESC;
```

**SQL (After Indexing):**

```sql
SELECT cs.* FROM Cost_Settlements cs JOIN Bookings b ON b.BookingID = cs.BookingID JOIN Rides r ON r.RideID = b.RideID WHERE b.Passenger_MemberID = :member_id OR r.Host_MemberID = :member_id ORDER BY cs.SettlementID DESC;
```

**Relevant Indexes:**

- idx_bookings_passenger_booked_at (Passenger_MemberID, Booked_At)
- idx_rides_host_ride_id (Host_MemberID, RideID)
- idx_settlements_settlement_booking (SettlementID, BookingID)

