import React, { useEffect, useState } from "react";
import geohash from "ngeohash";
import { MapContainer, Marker, Polyline, TileLayer } from "react-leaflet";

import { api } from "../api";

export default function MyBookingsPage() {
	const [bookings, setBookings] = useState([]);
	const [ridesById, setRidesById] = useState({});
	const [currentUser, setCurrentUser] = useState(null);
	const [expandedRideId, setExpandedRideId] = useState(null);
	const [pendingByRide, setPendingByRide] = useState({});
	const [pendingLoading, setPendingLoading] = useState(false);
	const [selectedPending, setSelectedPending] = useState(null);
	const [pendingRoutePath, setPendingRoutePath] = useState([]);
	const [oldRoutePath, setOldRoutePath] = useState([]);
	const [pendingRouteLoading, setPendingRouteLoading] = useState(false);
	const [showOldRoute, setShowOldRoute] = useState(true);
	const [showNewRoute, setShowNewRoute] = useState(true);
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
			setSelectedPending(null);
			setExpandedRideId(null);
			if (expandedRideId) {
				const data = await api.listPendingBookings(expandedRideId);
				setPendingByRide(prev => ({ ...prev, [expandedRideId]: data || [] }));
			}
		} catch (error) {
			setMessage(error.message || "Booking update failed");
		}
	}

	function decodeGeohash(geo) {
		try {
			const decoded = geohash.decode(geo);
			return [decoded.latitude, decoded.longitude];
		} catch {
			return null;
		}
	}

	async function fetchRouteData(points) {
		const coords = points
			.map(point => {
				if (!Array.isArray(point) || point.length !== 2) {
					return null;
				}
				const [lat, lng] = point;
				return `${lng},${lat}`;
			})
			.filter(Boolean)
			.join(";");
		if (!coords) {
			return { coordinates: [] };
		}
		const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`;
		const response = await fetch(url);
		const data = await response.json();
		const route = data?.routes?.[0];
		return {
			coordinates: route?.geometry?.coordinates || [],
		};
	}

	async function openPendingPreview(pending, ride) {
		setSelectedPending({ pending, ride });
		setShowOldRoute(true);
		setShowNewRoute(true);
		setPendingRouteLoading(true);
		try {
			const rideStart = decodeGeohash(ride?.Start_GeoHash);
			const rideEnd = decodeGeohash(ride?.End_GeoHash);
			const pickup = decodeGeohash(pending?.Pickup_GeoHash);
			const drop = decodeGeohash(pending?.Drop_GeoHash);
			if (!rideStart || !rideEnd || !pickup || !drop) {
				setPendingRoutePath([]);
				setOldRoutePath([]);
				return;
			}
			const [newRoute, oldRoute] = await Promise.all([
				fetchRouteData([rideStart, pickup, drop, rideEnd]),
				fetchRouteData([rideStart, rideEnd]),
			]);
			setPendingRoutePath(newRoute.coordinates.map(point => [point[1], point[0]]));
			setOldRoutePath(oldRoute.coordinates.map(point => [point[1], point[0]]));
		} catch {
			setPendingRoutePath([]);
			setOldRoutePath([]);
		} finally {
			setPendingRouteLoading(false);
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
													<strong>Booking #{pending.BookingID}</strong>
													<span>
														Pickup {pending.Pickup_GeoHash} → Drop {pending.Drop_GeoHash}
													</span>
													<button
														className="btn ghost"
														onClick={() => openPendingPreview(pending, ride)}
													>
														Preview & decide
													</button>
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
			{selectedPending ? (
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
							width: "min(900px, 96vw)",
							maxHeight: "90vh",
							overflow: "auto",
							background: "rgba(0, 0, 0, 0.95)",
						}}
					>
						<div className="section-title" style={{ marginBottom: 10 }}>
							<div>
								<h3>Pending booking #{selectedPending.pending.BookingID}</h3>
								<p className="message">
									Pickup {selectedPending.pending.Pickup_GeoHash} → Drop {selectedPending.pending.Drop_GeoHash}
								</p>
							</div>
							<button
								className="btn ghost"
								type="button"
								onClick={() => setSelectedPending(null)}
							>
								Close
							</button>
						</div>
						{pendingRouteLoading ? (
							<p className="message">Loading route preview...</p>
						) : null}
						{pendingRoutePath.length > 0 || oldRoutePath.length > 0 ? (
							<MapContainer
								center={(pendingRoutePath[0] || oldRoutePath[0]) ?? [0, 0]}
								zoom={12}
								style={{ height: 320, borderRadius: 12 }}
							>
								<TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
								{showOldRoute && oldRoutePath.length > 0 ? (
									<Polyline
										positions={oldRoutePath}
										pathOptions={{
											color: "#0d1b4c",
											weight: 8,
											opacity: 0.3,
										}}
									/>
								) : null}
								{showNewRoute && pendingRoutePath.length > 0 ? (
									<Polyline
										positions={pendingRoutePath}
										pathOptions={{ color: "#7b4dff", weight: 4, opacity: 0.9 }}
									/>
								) : null}
								{pendingRoutePath.length > 0 ? (
									<Marker position={pendingRoutePath[0]} />
								) : null}
								{pendingRoutePath.length > 0 ? (
									<Marker position={pendingRoutePath[pendingRoutePath.length - 1]} />
								) : null}
							</MapContainer>
						) : (
							<p className="message">Route preview unavailable for this booking.</p>
						)}
						<div className="chip-row" style={{ marginTop: 8 }}>
							<label className="pill">
								<input
									type="checkbox"
									checked={showOldRoute}
									onChange={event => setShowOldRoute(event.target.checked)}
								/>
								Old route (dark blue)
							</label>
							<label className="pill">
								<input
									type="checkbox"
									checked={showNewRoute}
									onChange={event => setShowNewRoute(event.target.checked)}
								/>
								New route (purple)
							</label>
						</div>
						<div className="chip-row" style={{ marginTop: 12 }}>
							<button
								className="btn primary"
								onClick={() => handleBookingAction(selectedPending.pending.BookingID, "accept")}
							>
								Accept booking
							</button>
							<button
								className="btn ghost"
								onClick={() => handleBookingAction(selectedPending.pending.BookingID, "reject")}
							>
								Reject booking
							</button>
						</div>
					</section>
				</div>
			) : null}
			<p className="message">{message}</p>
		</div>
	);
}
