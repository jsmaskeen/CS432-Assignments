import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";

export default function MyBookingsPage() {
	const [bookings, setBookings] = useState([]);
	const [ridesById, setRidesById] = useState({});
	const [currentUser, setCurrentUser] = useState(null);
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

	useEffect(() => {
		async function loadMissingRides() {
			if (!bookings.length) {
				return;
			}
			const missingIds = bookings
				.map(booking => booking.RideID)
				.filter(rideId => !ridesById[rideId]);
			if (!missingIds.length) {
				return;
			}
			try {
				const fetched = await Promise.all(
					missingIds.map(rideId => api.getRide(rideId).catch(() => null)),
				);
				setRidesById(prev => {
					const next = { ...prev };
					fetched.forEach(ride => {
						if (ride?.RideID) {
							next[ride.RideID] = ride;
						}
					});
					return next;
				});
			} catch (error) {
				setMessage(error.message || "Failed to load ride details");
			}
		}

		loadMissingRides();
	}, [bookings, ridesById]);

	useEffect(() => {
		async function loadMeta() {
			try {
				const [me, rides] = await Promise.all([
					api.me(),
					api.listRides({ only_open: false, limit: 100 }),
				]);
				setCurrentUser(me);
				const mapped = (rides || []).reduce((acc, ride) => {
					acc[ride.RideID] = ride;
					return acc;
				}, {});
				setRidesById(mapped);
			} catch (error) {
				setMessage(error.message || "Failed to load ride metadata");
			}
		}

		loadMeta();
	}, []);

	async function handleDeleteBooking(bookingId) {
		const confirmed = window.confirm("Delete this booking?");
		if (!confirmed) {
			return;
		}
		try {
			await api.deleteBooking(bookingId);
			setMessage("Booking deleted");
			loadBookings();
		} catch (error) {
			setMessage(error.message || "Failed to delete booking");
		}
	}


	return (
		<div className="page">
			<section className="card">
				<h2>My Bookings</h2>
				<div className="rides-list">
					{bookings.map(booking => {
						const ride = ridesById[booking.RideID];
						const isHost =
							currentUser && ride && ride.Host_MemberID === currentUser.member_id;
						return (
							<article key={booking.BookingID} className="card panel ride-card">
								<div className="section-title">
									<strong>Ride #{booking.RideID}</strong>
									<span className="pill">{booking.Booking_Status}</span>
								</div>
								<div className="list-inline">
									<span>Pickup: {booking.Pickup_GeoHash}</span>
									<span>→</span>
									<span>Drop: {booking.Drop_GeoHash}</span>
								</div>
								<div className="chip-row">
									<span className="pill success">
										Distance {booking.Distance_Travelled_KM} km
									</span>
									{ride ? (
										<span className="pill">
											Seats {ride.Available_Seats}/{ride.Max_Capacity}
										</span>
									) : null}
								</div>
								<div className="chip-row">
									{isHost ? (
										<Link className="btn ghost" to={`/rides/${booking.RideID}/manage`}>
											Manage Ride
										</Link>
									) : null}
									{booking.Booking_Status === "Confirmed" || isHost ? (
										<Link className="btn ghost" to={`/rides/${booking.RideID}/chat`}>
											Open Chat
										</Link>
									) : null}
									<button
										className="btn danger"
										onClick={() => handleDeleteBooking(booking.BookingID)}
									>
										Delete Booking
									</button>
								</div>
							</article>
						);
					})}
				</div>
			</section>
			<p className="message">{message}</p>
		</div>
	);
}
