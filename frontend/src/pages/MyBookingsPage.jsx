import React, { useEffect, useState } from "react";

import { api } from "../api";

export default function MyBookingsPage() {
	const [bookings, setBookings] = useState([]);
	const [ridesById, setRidesById] = useState({});
	const [currentUser, setCurrentUser] = useState(null);
	const [expandedRideId, setExpandedRideId] = useState(null);
	const [pendingByRide, setPendingByRide] = useState({});
	const [pendingLoading, setPendingLoading] = useState(false);
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

	async function toggleManageRide(rideId) {
		if (expandedRideId === rideId) {
			setExpandedRideId(null);
			return;
		}
		setExpandedRideId(rideId);
		setPendingLoading(true);
		try {
			const data = await api.listPendingBookings(rideId);
			setPendingByRide(prev => ({ ...prev, [rideId]: data || [] }));
		} catch (error) {
			setMessage(error.message || "Failed to load pending bookings");
		} finally {
			setPendingLoading(false);
		}
	}

	async function handleBookingAction(bookingId, action) {
		try {
			if (action === "accept") {
				await api.acceptBooking(bookingId);
			} else {
				await api.rejectBooking(bookingId);
			}
			setMessage(`Booking ${action}ed`);
			if (expandedRideId) {
				const data = await api.listPendingBookings(expandedRideId);
				setPendingByRide(prev => ({ ...prev, [expandedRideId]: data || [] }));
			}
		} catch (error) {
			setMessage(error.message || "Booking update failed");
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
							currentUser && ride && ride.Host_MemberID === currentUser.MemberID;
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
										<button
											className="btn ghost"
											onClick={() => toggleManageRide(booking.RideID)}
										>
											Manage Booking
										</button>
									) : null}
									<button
										className="btn danger"
										onClick={() => handleDeleteBooking(booking.BookingID)}
									>
										Delete Booking
									</button>
								</div>
								{isHost && expandedRideId === booking.RideID ? (
									<div className="card form-card compact">
										<h3>Pending bookings</h3>
										{pendingLoading ? (
											<p className="message">Loading pending bookings...</p>
										) : null}
										<ul className="booking-list">
											{(pendingByRide[booking.RideID] || []).map(pending => (
												<li key={pending.BookingID}>
													<span>Booking #{pending.BookingID}</span>
													<span>
														Pickup {pending.Pickup_GeoHash} → Drop {pending.Drop_GeoHash}
													</span>
													<div className="chip-row">
														<button
															className="btn primary"
															onClick={() => handleBookingAction(pending.BookingID, "accept")}
														>
															Accept
														</button>
														<button
															className="btn ghost"
															onClick={() => handleBookingAction(pending.BookingID, "reject")}
														>
															Reject
														</button>
													</div>
												</li>
											))}
											{!pendingLoading && (pendingByRide[booking.RideID] || []).length === 0 ? (
												<li>No pending bookings.</li>
											) : null}
										</ul>
									</div>
								) : null}
							</article>
						);
					})}
				</div>
			</section>
			<p className="message">{message}</p>
		</div>
	);
}
