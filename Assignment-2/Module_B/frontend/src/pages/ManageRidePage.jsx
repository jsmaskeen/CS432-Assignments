import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import geohash from "ngeohash";
import { MapContainer, Marker, Polyline, TileLayer } from "react-leaflet";

import { api } from "../api";

export default function ManageRidePage() {
	const { rideId } = useParams();
	const navigate = useNavigate();
	const [ride, setRide] = useState(null);
	const [form, setForm] = useState({
		vehicle_type: "",
		max_capacity: "",
		filled_seats: "",
	});
	const [pendingRequests, setPendingRequests] = useState([]);
	const [pendingLoading, setPendingLoading] = useState(false);
	const [selectedPending, setSelectedPending] = useState(null);
	const [pendingRoutePath, setPendingRoutePath] = useState([]);
	const [oldRoutePath, setOldRoutePath] = useState([]);
	const [pendingRouteLoading, setPendingRouteLoading] = useState(false);
	const [showOldRoute, setShowOldRoute] = useState(true);
	const [showNewRoute, setShowNewRoute] = useState(true);
	const [confirmedBookings, setConfirmedBookings] = useState([]);
	const [confirmedStops, setConfirmedStops] = useState([]);
	const [settlementByBooking, setSettlementByBooking] = useState({});
	const [settlementsLoading, setSettlementsLoading] = useState(false);
	const [message, setMessage] = useState("");
	const [actionLoading, setActionLoading] = useState(false);

	function distanceKm(a, b) {
		if (!a || !b) return Number.POSITIVE_INFINITY;
		const [lat1, lon1] = a;
		const [lat2, lon2] = b;
		const rad = Math.PI / 180;
		const dLat = (lat2 - lat1) * rad;
		const dLon = (lon2 - lon1) * rad;
		const lat1Rad = lat1 * rad;
		const lat2Rad = lat2 * rad;
		const sinLat = Math.sin(dLat / 2);
		const sinLon = Math.sin(dLon / 2);
		const h = sinLat * sinLat + Math.cos(lat1Rad) * Math.cos(lat2Rad) * sinLon * sinLon;
		return 6371 * 2 * Math.asin(Math.min(1, Math.sqrt(h)));
	}

	function orderStopsByDistance(start, stops) {
		if (!start || !Array.isArray(stops) || stops.length === 0) {
			return stops || [];
		}
		const remaining = [...stops];
		const ordered = [];
		let current = start;
		while (remaining.length > 0) {
			let bestIndex = 0;
			let bestDistance = distanceKm(current, remaining[0]);
			for (let i = 1; i < remaining.length; i += 1) {
				const candidateDistance = distanceKm(current, remaining[i]);
				if (candidateDistance < bestDistance) {
					bestDistance = candidateDistance;
					bestIndex = i;
				}
			}
			const next = remaining.splice(bestIndex, 1)[0];
			ordered.push(next);
			current = next;
		}
		return ordered;
	}
	const orderedConfirmedStops = React.useMemo(() => {
		const start = decodeGeohash(ride?.Start_GeoHash);
		return orderStopsByDistance(start, confirmedStops);
	}, [ride?.Start_GeoHash, confirmedStops]);

	useEffect(() => {
		async function loadRide() {
			try {
				const data = await api.getRide(rideId);
				setRide(data);
				const filled = Number(data?.Max_Capacity ?? 0) - Number(data?.Available_Seats ?? 0);
				setForm({
					vehicle_type: data?.Vehicle_Type || "",
					max_capacity: String(data?.Max_Capacity ?? ""),
					filled_seats: String(Math.max(0, filled)),
				});
			} catch (error) {
				setMessage(error.message || "Failed to load ride details");
			}
		}

		if (rideId) {
			loadRide();
		}
	}, [rideId]);

	useEffect(() => {
		async function loadPending() {
			if (!rideId) {
				return;
			}
			setPendingLoading(true);
			try {
				const data = await api.listPendingBookings(rideId);
				setPendingRequests(data || []);
			} catch (error) {
				setMessage(error.message || "Failed to load pending requests");
			} finally {
				setPendingLoading(false);
			}
		}

		loadPending();
	}, [rideId]);

	useEffect(() => {
		let cancelled = false;
		if (!rideId) {
			setConfirmedBookings([]);
			setConfirmedStops([]);
			return () => {};
		}

		api.listConfirmedBookingStops(rideId)
			.then(data => {
				if (cancelled) {
					return;
				}
				const bookings = data || [];
				setConfirmedBookings(bookings);
				const stops = bookings.flatMap(booking => {
					const pickup = decodeGeohash(booking.Pickup_GeoHash);
					const drop = decodeGeohash(booking.Drop_GeoHash);
					return [pickup, drop].filter(Boolean);
				});
				setConfirmedStops(stops);
			})
			.catch(() => {
				if (!cancelled) {
					setConfirmedBookings([]);
					setConfirmedStops([]);
				}
			});

		return () => {
			cancelled = true;
		};
	}, [rideId]);

	useEffect(() => {
		let cancelled = false;

		async function loadSettlementsForConfirmed() {
			if (!confirmedBookings.length) {
				setSettlementByBooking({});
				setSettlementsLoading(false);
				return;
			}

			setSettlementsLoading(true);
			try {
				const entries = await Promise.all(
					confirmedBookings.map(async booking => {
						try {
							const settlement = await api.getBookingSettlement(booking.BookingID);
							return [booking.BookingID, settlement || null];
						} catch {
							return [booking.BookingID, null];
						}
					}),
				);

				if (cancelled) {
					return;
				}

				const next = entries.reduce((acc, [bookingId, settlement]) => {
					acc[bookingId] = settlement;
					return acc;
				}, {});
				setSettlementByBooking(next);
			} finally {
				if (!cancelled) {
					setSettlementsLoading(false);
				}
			}
		}

		loadSettlementsForConfirmed();

		return () => {
			cancelled = true;
		};
	}, [confirmedBookings]);

	async function handleSubmit(event) {
		event.preventDefault();
		try {
			const payload = {
				vehicle_type: form.vehicle_type,
				max_capacity: Number(form.max_capacity),
				filled_seats: Number(form.filled_seats),
			};
			await api.updateRide(rideId, payload);
			setMessage("Ride updated");
			const refreshed = await api.getRide(rideId);
			setRide(refreshed);
		} catch (error) {
			setMessage(error.message || "Failed to update ride");
		}
	}

	async function handleRideAction(action) {
		if (!rideId) {
			return;
		}
		setActionLoading(true);
		try {
			const updated =
				action === "start" ? await api.startRide(rideId) : await api.endRide(rideId);
			setRide(updated);
			setMessage(`Ride ${action === "start" ? "started" : "ended"}`);
		} catch (error) {
			setMessage(error.message || `Failed to ${action} ride`);
		} finally {
			setActionLoading(false);
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

	async function openPendingPreview(pending) {
		setSelectedPending(pending);
		setShowOldRoute(true);
		setShowNewRoute(true);
		setPendingRouteLoading(true);
		setPendingRoutePath([]);
		setOldRoutePath([]);
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
			const combinedStops = [...confirmedStops, pickup, drop];
			const orderedStops = orderStopsByDistance(rideStart, combinedStops);
			const [newRoute, oldRoute] = await Promise.all([
				fetchRouteData([rideStart, ...orderedStops, rideEnd]),
				fetchRouteData([rideStart, ...orderedConfirmedStops, rideEnd]),
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

	async function handlePendingAction(bookingId, action) {
		try {
			if (action === "accept") {
				await api.acceptBooking(bookingId);
			} else {
				await api.rejectBooking(bookingId);
			}
			setMessage(`Booking ${action}ed`);
			setSelectedPending(null);
			const data = await api.listPendingBookings(rideId);
			setPendingRequests(data || []);
			const confirmed = await api.listConfirmedBookingStops(rideId);
			setConfirmedBookings(confirmed || []);
			const stops = (confirmed || []).flatMap(booking => {
				const pickup = decodeGeohash(booking.Pickup_GeoHash);
				const drop = decodeGeohash(booking.Drop_GeoHash);
				return [pickup, drop].filter(Boolean);
			});
			setConfirmedStops(stops);
		} catch (error) {
			setMessage(error.message || "Booking update failed");
		}
	}

	async function refreshSettlements() {
		if (!confirmedBookings.length) {
			setSettlementByBooking({});
			return;
		}
		setSettlementsLoading(true);
		try {
			const entries = await Promise.all(
				confirmedBookings.map(async booking => {
					try {
						const settlement = await api.getBookingSettlement(booking.BookingID);
						return [booking.BookingID, settlement || null];
					} catch {
						return [booking.BookingID, null];
					}
				}),
			);
			const next = entries.reduce((acc, [bookingId, settlement]) => {
				acc[bookingId] = settlement;
				return acc;
			}, {});
			setSettlementByBooking(next);
			setMessage("Settlements refreshed");
		} catch {
			setMessage("Failed to refresh settlements");
		} finally {
			setSettlementsLoading(false);
		}
	}

	return (
		<div className="page">
			<section className="card panel">
				<div className="section-title">
					<div>
						<h2>Manage Ride #{rideId}</h2>
						<p className="message">Update vehicle type, max seats, and filled seats.</p>
					</div>
					<div className="chip-row">
						<Link to="/bookings" className="btn ghost">
							Back to bookings
						</Link>
						<button className="btn ghost" type="button" onClick={() => navigate(-1)}>
							Back
						</button>
					</div>
				</div>
				{ride && ride.Ride_Status !== "Completed" ? (
					<div className="chip-row" style={{ marginBottom: 12 }}>
						<span className="pill">Status: {ride.Ride_Status}</span>
						<button
							className="btn primary"
							type="button"
							onClick={() =>
								handleRideAction(ride.Ride_Status === "Started" ? "end" : "start")
							}
							disabled={
								actionLoading ||
								!["Open", "Full", "Started"].includes(ride.Ride_Status)
							}
						>
							{ride.Ride_Status === "Started" ? "End ride" : "Start ride"}
						</button>
					</div>
				) : null}
				<form className="form-card compact" onSubmit={handleSubmit}>
					<label>
						<span className="input-label">Vehicle type</span>
						<input
							placeholder="Vehicle type"
							value={form.vehicle_type}
							onChange={event =>
								setForm(prev => ({ ...prev, vehicle_type: event.target.value }))
							}
							required
						/>
					</label>
					<label>
						<span className="input-label">Max capacity</span>
						<input
							type="number"
							min="1"
							max="10"
							placeholder="Max capacity"
							value={form.max_capacity}
							onChange={event =>
								setForm(prev => ({ ...prev, max_capacity: event.target.value }))
							}
							required
						/>
					</label>
					<label>
						<span className="input-label">Filled seats</span>
						<input
							type="number"
							min="0"
							placeholder="Filled seats"
							value={form.filled_seats}
							onChange={event =>
								setForm(prev => ({ ...prev, filled_seats: event.target.value }))
							}
							required
						/>
					</label>
					{ride ? (
						<p className="message">Current available seats: {ride.Available_Seats}</p>
					) : null}
					<button className="btn primary" type="submit">
						Save changes
					</button>
				</form>
			</section>
			<section className="card panel">
				<div className="section-title">
					<h3>Confirmed bookings</h3>
					<span className="pill">{confirmedBookings.length}</span>
				</div>
				<ul className="booking-list">
					{confirmedBookings.map(booking => (
						<li key={`confirmed-${booking.BookingID}`}>
							<strong>Booking #{booking.BookingID}</strong>
							<span>
								Rider {booking.Passenger_Name || "Unknown"} • Rating{" "}
								{booking.Passenger_Rating ?? "-"}
							</span>
							<span>
								Pickup {booking.Pickup_GeoHash} → Drop {booking.Drop_GeoHash}
							</span>
						</li>
					))}
					{confirmedBookings.length === 0 ? <li>No confirmed bookings yet.</li> : null}
				</ul>
			</section>
			<section className="card panel">
				<div className="section-title">
					<h3>Settlements</h3>
					<div className="chip-row">
						<span className="pill">{confirmedBookings.length} bookings</span>
						<button
							className="btn ghost"
							type="button"
							onClick={refreshSettlements}
							disabled={settlementsLoading}
						>
							{settlementsLoading ? "Refreshing..." : "Refresh"}
						</button>
					</div>
				</div>
				{settlementsLoading ? <p className="message">Loading settlements...</p> : null}
				<ul className="booking-list">
					{confirmedBookings.map(booking => {
						const settlement = settlementByBooking[booking.BookingID] || null;
						const status = settlement?.Payment_Status || "NotGenerated";
						const isSettled = status === "Settled";
						return (
							<li key={`settlement-${booking.BookingID}`}>
								<strong>Booking #{booking.BookingID}</strong>
								<span>
									Rider {booking.Passenger_Name || "Unknown"} • Status{" "}
									{booking.Booking_Status}
								</span>
								<span>
									Settlement:{" "}
									{status === "NotGenerated" ? "Not generated yet" : status}
								</span>
								{settlement ? (
									<span>
										Amount: ₹
										{Number(settlement.Calculated_Cost || 0).toFixed(2)}
									</span>
								) : null}
								<span className={`pill ${isSettled ? "success" : "warn"}`}>
									{isSettled ? "Settled" : "Unpaid / Pending"}
								</span>
							</li>
						);
					})}
					{!settlementsLoading && confirmedBookings.length === 0 ? (
						<li>No confirmed bookings to settle yet.</li>
					) : null}
				</ul>
			</section>
			<section className="card panel">
				<div className="section-title">
					<h3>Pending requests</h3>
					<span className="pill">{pendingRequests.length}</span>
				</div>
				{pendingLoading ? <p className="message">Loading pending requests...</p> : null}
				<ul className="booking-list">
					{pendingRequests.map(pending => (
						<li key={pending.BookingID}>
							<strong>Booking #{pending.BookingID}</strong>
							<span>
								Rider {pending.Passenger_Name || "Unknown"} • Rating{" "}
								{pending.Passenger_Rating ?? "-"}
							</span>
							<span>
								Pickup {pending.Pickup_GeoHash} → Drop {pending.Drop_GeoHash}
							</span>
							<button
								className="btn ghost"
								onClick={() => openPendingPreview(pending)}
							>
								Preview & decide
							</button>
						</li>
					))}
					{!pendingLoading && pendingRequests.length === 0 ? (
						<li>No pending requests.</li>
					) : null}
				</ul>
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
								<h3>Pending booking #{selectedPending.BookingID}</h3>
								<p className="message">
									Pickup {selectedPending.Pickup_GeoHash} → Drop{" "}
									{selectedPending.Drop_GeoHash}
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
									<Marker
										position={pendingRoutePath[pendingRoutePath.length - 1]}
									/>
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
								onClick={() =>
									handlePendingAction(selectedPending.BookingID, "accept")
								}
							>
								Accept booking
							</button>
							<button
								className="btn ghost"
								onClick={() =>
									handlePendingAction(selectedPending.BookingID, "reject")
								}
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
