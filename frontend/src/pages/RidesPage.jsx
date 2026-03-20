import React from "react";
import { useEffect, useState } from "react";

import { api } from "../api";

const initialRide = {
	start_geohash: "",
	end_geohash: "",
	departure_time: "",
	vehicle_type: "Sedan",
	max_capacity: 4,
	base_fare_per_km: "12.00",
};

const initialBooking = {
	pickup_geohash: "",
	drop_geohash: "",
	distance_travelled_km: "10.0",
};

export default function RidesPage() {
	const [rides, setRides] = useState([]);
	const [myBookings, setMyBookings] = useState([]);
	const [rideForm, setRideForm] = useState(initialRide);
	const [bookingForm, setBookingForm] = useState(initialBooking);
	const [selectedRideId, setSelectedRideId] = useState(null);
	const [message, setMessage] = useState("");

	async function loadData() {
		try {
			const [rideData, bookingData] = await Promise.all([api.listRides(), api.myBookings()]);
			setRides(rideData);
			setMyBookings(bookingData);
		} catch (error) {
			setMessage(error.message);
		}
	}

	useEffect(() => {
		loadData();
	}, []);

	async function handleCreateRide(event) {
		event.preventDefault();
		setMessage("Creating ride...");
		try {
			await api.createRide({
				...rideForm,
				max_capacity: Number(rideForm.max_capacity),
				base_fare_per_km: Number(rideForm.base_fare_per_km),
			});
			setRideForm(initialRide);
			setMessage("Ride created.");
			loadData();
		} catch (error) {
			setMessage(error.message);
		}
	}

	async function handleBookRide(event) {
		event.preventDefault();
		if (!selectedRideId) {
			setMessage("Select a ride first.");
			return;
		}

		setMessage("Booking ride...");
		try {
			await api.bookRide(selectedRideId, {
				...bookingForm,
				distance_travelled_km: Number(bookingForm.distance_travelled_km),
			});
			setBookingForm(initialBooking);
			setSelectedRideId(null);
			setMessage("Booking successful.");
			loadData();
		} catch (error) {
			setMessage(error.message);
		}
	}

	return (
		<div className="page rides-page">
			<div className="grid-two">
				<section className="card">
					<h2>Open rides</h2>
					<div className="rides-list">
						{rides.map(ride => (
							<button
								key={ride.RideID}
								className={`ride-card ${selectedRideId === ride.RideID ? "selected" : ""}`}
								onClick={() => setSelectedRideId(ride.RideID)}
							>
								<strong>Ride #{ride.RideID}</strong>
								<span>
									{ride.Start_GeoHash}
									{" -> "}
									{ride.End_GeoHash}
								</span>
								<span>
									{ride.Vehicle_Type} | Seats: {ride.Available_Seats}/
									{ride.Max_Capacity}
								</span>
								<span>Fare/km: {ride.Base_Fare_Per_KM}</span>
							</button>
						))}
					</div>
				</section>

				<section className="card">
					<h2>Create ride</h2>
					<form className="form-card compact" onSubmit={handleCreateRide}>
						<input
							placeholder="Start geohash"
							value={rideForm.start_geohash}
							onChange={e =>
								setRideForm({ ...rideForm, start_geohash: e.target.value })
							}
							required
						/>
						<input
							placeholder="End geohash"
							value={rideForm.end_geohash}
							onChange={e =>
								setRideForm({ ...rideForm, end_geohash: e.target.value })
							}
							required
						/>
						<input
							type="datetime-local"
							value={rideForm.departure_time}
							onChange={e =>
								setRideForm({ ...rideForm, departure_time: e.target.value })
							}
							required
						/>
						<input
							placeholder="Vehicle type"
							value={rideForm.vehicle_type}
							onChange={e =>
								setRideForm({ ...rideForm, vehicle_type: e.target.value })
							}
							required
						/>
						<input
							type="number"
							min="1"
							max="10"
							placeholder="Max capacity"
							value={rideForm.max_capacity}
							onChange={e =>
								setRideForm({ ...rideForm, max_capacity: e.target.value })
							}
							required
						/>
						<input
							type="number"
							min="1"
							step="0.01"
							placeholder="Fare per km"
							value={rideForm.base_fare_per_km}
							onChange={e =>
								setRideForm({ ...rideForm, base_fare_per_km: e.target.value })
							}
							required
						/>
						<button className="btn primary" type="submit">
							Publish Ride
						</button>
					</form>
				</section>
			</div>

			<div className="grid-two">
				<section className="card">
					<h2>Book selected ride</h2>
					<form className="form-card compact" onSubmit={handleBookRide}>
						<input
							placeholder="Pickup geohash"
							value={bookingForm.pickup_geohash}
							onChange={e =>
								setBookingForm({ ...bookingForm, pickup_geohash: e.target.value })
							}
							required
						/>
						<input
							placeholder="Drop geohash"
							value={bookingForm.drop_geohash}
							onChange={e =>
								setBookingForm({ ...bookingForm, drop_geohash: e.target.value })
							}
							required
						/>
						<input
							type="number"
							min="0.1"
							step="0.1"
							placeholder="Distance km"
							value={bookingForm.distance_travelled_km}
							onChange={e =>
								setBookingForm({
									...bookingForm,
									distance_travelled_km: e.target.value,
								})
							}
							required
						/>
						<button className="btn primary" type="submit">
							Book Ride #{selectedRideId ?? "?"}
						</button>
					</form>
				</section>

				<section className="card">
					<h2>My bookings</h2>
					<ul className="booking-list">
						{myBookings.map(booking => (
							<li key={booking.BookingID}>
								<strong>Booking #{booking.BookingID}</strong>
								<span>
									Ride #{booking.RideID} | {booking.Booking_Status}
								</span>
								<span>
									{booking.Pickup_GeoHash}
									{" -> "}
									{booking.Drop_GeoHash}
								</span>
							</li>
						))}
					</ul>
				</section>
			</div>

			<p className="message">{message}</p>
		</div>
	);
}
