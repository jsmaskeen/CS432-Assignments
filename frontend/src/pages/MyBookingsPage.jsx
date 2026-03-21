import React, { useEffect, useState } from "react";

import { api } from "../api";

export default function MyBookingsPage() {
	const [bookings, setBookings] = useState([]);
	const [message, setMessage] = useState("");

	async function loadBookings() {
		try {
			const data = await api.myBookings();
			setBookings(data || []);
			setMessage(`Loaded ${data.length} bookings`);
		} catch (error) {
			setMessage(error.message);
		}
	}

	useEffect(() => {
		loadBookings();
	}, []);

	return (
		<div className="page">
			<section className="card">
				<h2>My Bookings</h2>
				<ul className="booking-list">
					{bookings.map(booking => (
						<li key={booking.BookingID}>
							<strong>Ride #{booking.RideID}</strong>
							<span>Status: {booking.Booking_Status}</span>
							<span>
								Pickup: {booking.Pickup_GeoHash} → Drop: {booking.Drop_GeoHash}
							</span>
							<span>Distance: {booking.Distance_Travelled_KM} km</span>
						</li>
					))}
				</ul>
			</section>
			<p className="message">{message}</p>
		</div>
	);
}
