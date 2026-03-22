import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";

export default function MyBookingsPage() {
	const [bookings, setBookings] = useState([]);
	const [ridesById, setRidesById] = useState({});
	const [currentUser, setCurrentUser] = useState(null);
	const [message, setMessage] = useState("");
	const [reviewRideId, setReviewRideId] = useState(null);
	const [reviewTargets, setReviewTargets] = useState([]);
	const [reviewForm, setReviewForm] = useState({});
	const [reviewLoading, setReviewLoading] = useState(false);
	const [autoPrompted, setAutoPrompted] = useState(false);

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

	async function openReviewPrompt(rideId) {
		if (!rideId || !currentUser) {
			return;
		}
		setReviewLoading(true);
		try {
			const [participants, reviews] = await Promise.all([
				api.listRideReviewParticipants(rideId),
				api.listRideReviews(rideId),
			]);
			const reviewedIds = new Set(
				(reviews || [])
					.filter(review => review.Reviewer_MemberID === currentUser.member_id)
					.map(review => review.Reviewee_MemberID),
			);
			const targets = (participants || [])
				.filter(person => person.MemberID !== currentUser.member_id)
				.filter(person => !reviewedIds.has(person.MemberID));
			setReviewTargets(targets);
			setReviewForm(prev => {
				const next = { ...prev };
				targets.forEach(person => {
					if (!next[person.MemberID]) {
						next[person.MemberID] = { rating: 5, comments: "" };
					}
				});
				return next;
			});
			setReviewRideId(rideId);
		} catch (error) {
			setMessage(error.message || "Failed to load review targets");
		} finally {
			setReviewLoading(false);
		}
	}

	async function submitReview(rideId, memberId) {
		const payload = reviewForm[memberId];
		if (!payload) {
			return;
		}
		setReviewLoading(true);
		try {
			await api.createReview({
				ride_id: Number(rideId),
				reviewee_member_id: Number(memberId),
				rating: Number(payload.rating),
				comments: payload.comments || undefined,
			});
			setReviewTargets(prev => prev.filter(target => target.MemberID !== memberId));
			setMessage("Review submitted");
		} catch (error) {
			setMessage(error.message || "Failed to submit review");
		} finally {
			setReviewLoading(false);
		}
	}

	useEffect(() => {
		if (autoPrompted || !currentUser) {
			return;
		}
		const completed = bookings.find(booking => {
			const ride = ridesById[booking.RideID];
			return ride && ride.Ride_Status === "Completed";
		});
		if (completed) {
			setAutoPrompted(true);
			openReviewPrompt(completed.RideID);
		}
	}, [autoPrompted, bookings, currentUser, ridesById]);


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
									{ride && ride.Ride_Status === "Completed" ? (
										<button
											className="btn ghost"
											onClick={() => openReviewPrompt(booking.RideID)}
										>
											Review riders
										</button>
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
			{reviewRideId ? (
				<div
					style={{
						position: "fixed",
						inset: 0,
						background: "rgba(0, 0, 0, 0.55)",
						display: "grid",
						placeItems: "center",
						zIndex: 1000,
					}}
				>
					<section
						className="card"
						style={{
							width: "min(760px, 94vw)",
							maxHeight: "85vh",
							overflow: "auto",
							background: "rgba(0, 0, 0, 0.95)",
						}}
					>
						<div className="section-title">
							<div>
								<h3>Review participants</h3>
								<p className="message">Ride #{reviewRideId}</p>
							</div>
							<button
								className="btn ghost"
								onClick={() => setReviewRideId(null)}
							>
								Close
							</button>
						</div>
						{reviewLoading ? <p className="message">Loading reviews...</p> : null}
						{reviewTargets.length === 0 ? (
							<p className="message">All reviews completed for this ride.</p>
						) : null}
						<div className="rides-list">
							{reviewTargets.map(target => (
								<div key={target.MemberID} className="card panel">
									<div className="section-title">
										<strong>{target.Full_Name}</strong>
										<span className="pill">{target.Role}</span>
									</div>
									<div className="chip-row">
										<label>
											<span className="input-label">Rating (1-5)</span>
											<input
												type="number"
												min="1"
												max="5"
												value={reviewForm[target.MemberID]?.rating ?? 5}
												onChange={event =>
													setReviewForm(prev => ({
														...prev,
														[target.MemberID]: {
															...prev[target.MemberID],
															rating: event.target.value,
														},
													}))
												}
											/>
										</label>
										<label style={{ flex: 1 }}>
											<span className="input-label">Comments</span>
											<input
												placeholder="Optional feedback"
												value={reviewForm[target.MemberID]?.comments ?? ""}
												onChange={event =>
													setReviewForm(prev => ({
														...prev,
														[target.MemberID]: {
															...prev[target.MemberID],
															comments: event.target.value,
														},
													}))
												}
											/>
										</label>
										<button
											className="btn primary"
												onClick={() => submitReview(reviewRideId, target.MemberID)}
											disabled={reviewLoading}
										>
											Submit
										</button>
									</div>
								</div>
							))}
						</div>
					</section>
				</div>
			) : null}
			<p className="message">{message}</p>
		</div>
	);
}
