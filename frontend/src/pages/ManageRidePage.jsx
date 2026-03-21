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
	const [message, setMessage] = useState("");

	useEffect(() => {
		async function loadRide() {
			try {
				const data = await api.getRide(rideId);
				setRide(data);
				const filled =
					Number(data?.Max_Capacity ?? 0) - Number(data?.Available_Seats ?? 0);
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
		} catch (error) {
			setMessage(error.message || "Booking update failed");
		}
	}

	return (
		<div className="page">
			<section className="card panel">
				<div className="section-title">
					<div>
						<h2>Manage Ride #{rideId}</h2>
						<p className="message">
							Update vehicle type, max seats, and filled seats.
						</p>
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
						<p className="message">
							Current available seats: {ride.Available_Seats}
						</p>
					) : null}
					<button className="btn primary" type="submit">
						Save changes
					</button>
				</form>
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
									Pickup {selectedPending.Pickup_GeoHash} → Drop {selectedPending.Drop_GeoHash}
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
								onClick={() => handlePendingAction(selectedPending.BookingID, "accept")}
							>
								Accept booking
							</button>
							<button
								className="btn ghost"
								onClick={() => handlePendingAction(selectedPending.BookingID, "reject")}
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
