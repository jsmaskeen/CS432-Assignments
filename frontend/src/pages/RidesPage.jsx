import React from "react";
import { useEffect, useState } from "react";
import geohash from "ngeohash";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";

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

const startIcon = new L.Icon({
	iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
});

const endIcon = new L.Icon({
	iconUrl:
		"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
});

const selectedStartIcon = new L.Icon({
	iconUrl:
		"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
});

function FocusSelectedRide({ selectedRide }) {
	const map = useMap();

	useEffect(() => {
		if (!selectedRide) {
			return;
		}

		const bounds = L.latLngBounds([selectedRide.start, selectedRide.end]);
		map.fitBounds(bounds, { padding: [80, 80], maxZoom: 13 });
	}, [map, selectedRide]);

	return null;
}

function MapClickCapture({ onPick }) {
	useMapEvents({
		click(event) {
			onPick(event.latlng);
		},
	});

	return null;
}

function decodeGeohash(geo) {
	try {
		const decoded = geohash.decode(geo);
		return [decoded.latitude, decoded.longitude];
	} catch {
		return null;
	}
}

function toGoogleDirectionsUrl(start, end) {
	return `https://www.google.com/maps/dir/?api=1&origin=${start[0]},${start[1]}&destination=${end[0]},${end[1]}&travelmode=driving`;
}

export default function RidesPage() {
	const [currentUser, setCurrentUser] = useState(null);
	const [rides, setRides] = useState([]);
	const [myBookings, setMyBookings] = useState([]);
	const [selectedRideRoute, setSelectedRideRoute] = useState([]);
	const [promoteUsername, setPromoteUsername] = useState("");
	const [rideForm, setRideForm] = useState(initialRide);
	const [ridePickTarget, setRidePickTarget] = useState("start");
	const [bookingForm, setBookingForm] = useState(initialBooking);
	const [bookingPickTarget, setBookingPickTarget] = useState("pickup");
	const [activeMapPicker, setActiveMapPicker] = useState("ride");
	const [selectedRideId, setSelectedRideId] = useState(null);
	const [message, setMessage] = useState("");

	const mappedRides = rides
		.map(ride => {
			const start = decodeGeohash(ride.Start_GeoHash);
			const end = decodeGeohash(ride.End_GeoHash);
			if (!start || !end) {
				return null;
			}
			return { ...ride, start, end };
		})
		.filter(Boolean);

	const selectedRide = mappedRides.find(ride => ride.RideID === selectedRideId) || null;
	const draftStart = decodeGeohash(rideForm.start_geohash);
	const draftEnd = decodeGeohash(rideForm.end_geohash);
	const draftPickup = decodeGeohash(bookingForm.pickup_geohash);
	const draftDrop = decodeGeohash(bookingForm.drop_geohash);
	const mapCenter = selectedRide?.start || mappedRides[0]?.start || [23.2156, 72.6369]; // IITGN default area

	function handleMapPick(latlng) {
		const hash = geohash.encode(latlng.lat, latlng.lng, 7);

		if (activeMapPicker === "ride") {
			setRideForm(previous => {
				if (ridePickTarget === "start") {
					return { ...previous, start_geohash: hash };
				}
				return { ...previous, end_geohash: hash };
			});

			setMessage(`Picked ride ${ridePickTarget} geohash: ${hash}`);
			if (ridePickTarget === "start") {
				setRidePickTarget("end");
			}
			return;
		}

		setBookingForm(previous => {
			if (bookingPickTarget === "pickup") {
				return { ...previous, pickup_geohash: hash };
			}
			return { ...previous, drop_geohash: hash };
		});

		setMessage(`Picked booking ${bookingPickTarget} geohash: ${hash}`);
		if (bookingPickTarget === "pickup") {
			setBookingPickTarget("drop");
		}
	}

	async function loadData() {
		try {
			const [meData, rideData, bookingData] = await Promise.all([
				api.me(),
				api.listRides(),
				api.myBookings(),
			]);
			setCurrentUser(meData);
			setRides(rideData);
			setMyBookings(bookingData);
		} catch (error) {
			setMessage(error.message);
		}
	}

	useEffect(() => {
		loadData();
	}, []);

	useEffect(() => {
		async function loadRoute() {
			if (!selectedRide) {
				setSelectedRideRoute([]);
				return;
			}

			const [sLat, sLng] = selectedRide.start;
			const [eLat, eLng] = selectedRide.end;
			const url = `https://router.project-osrm.org/route/v1/driving/${sLng},${sLat};${eLng},${eLat}?overview=full&geometries=geojson`;
			try {
				const response = await fetch(url);
				const data = await response.json();
				const points = data?.routes?.[0]?.geometry?.coordinates || [];
				setSelectedRideRoute(points.map(point => [point[1], point[0]]));
			} catch {
				setSelectedRideRoute([]);
			}
		}

		loadRoute();
	}, [selectedRideId, rides]);

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

	async function handlePromote(event) {
		event.preventDefault();
		setMessage("Promoting user...");
		try {
			const result = await api.promoteToAdmin(promoteUsername);
			setMessage(result.message || "User promoted");
			setPromoteUsername("");
		} catch (error) {
			setMessage(error.message);
		}
	}

	return (
		<div className="page rides-page">
			{currentUser ? (
				<p className="message">
					Logged in as {currentUser.username} ({currentUser.role})
				</p>
			) : null}

			{currentUser?.role === "admin" ? (
				<section className="card">
					<h2>Admin actions</h2>
					<form className="form-card compact" onSubmit={handlePromote}>
						<input
							placeholder="Username to promote"
							value={promoteUsername}
							onChange={e => setPromoteUsername(e.target.value)}
							required
						/>
						<button className="btn primary" type="submit">
							Promote To Admin
						</button>
					</form>
				</section>
			) : null}

			<section className="card map-stage">
				<div className="map-head">
					<h2>Live Rides Map</h2>
					<p>
						Click a ride card to focus the map and mark that ride's start/end locations.
						A road route overlay and Google Maps link are shown for the selected ride. You can also click on the map to fill geohashes in Create Ride and Book Selected Ride.
					</p>
				</div>
				<MapContainer center={mapCenter} zoom={11} className="rides-map">
					<TileLayer
						attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
						url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
					/>
					<FocusSelectedRide selectedRide={selectedRide} />
					<MapClickCapture onPick={handleMapPick} />

					{mappedRides.map(ride => (
						<React.Fragment key={`map-${ride.RideID}`}>
							<Polyline
								positions={[ride.start, ride.end]}
								pathOptions={{
									color: ride.RideID === selectedRideId ? "#1f7aff" : "#7f9fd6",
									dashArray: "8 8",
									weight: ride.RideID === selectedRideId ? 4 : 2,
								}}
							/>
						</React.Fragment>
					))}

					{selectedRide ? (
						<>
							<Marker position={selectedRide.start} icon={selectedStartIcon}>
								<Popup>Ride #{selectedRide.RideID} start</Popup>
							</Marker>
							<Marker position={selectedRide.end} icon={endIcon}>
								<Popup>Ride #{selectedRide.RideID} destination</Popup>
							</Marker>
						</>
					) : null}

					{draftStart ? (
						<Marker position={draftStart} icon={selectedStartIcon}>
							<Popup>Create ride start ({rideForm.start_geohash})</Popup>
						</Marker>
					) : null}
					{draftEnd ? (
						<Marker position={draftEnd} icon={endIcon}>
							<Popup>Create ride end ({rideForm.end_geohash})</Popup>
						</Marker>
					) : null}
					{draftStart && draftEnd ? (
						<Polyline positions={[draftStart, draftEnd]} pathOptions={{ color: "#34a853", weight: 3 }} />
					) : null}
					{draftPickup ? (
						<Marker position={draftPickup} icon={startIcon}>
							<Popup>Booking pickup ({bookingForm.pickup_geohash})</Popup>
						</Marker>
					) : null}
					{draftDrop ? (
						<Marker position={draftDrop} icon={endIcon}>
							<Popup>Booking drop ({bookingForm.drop_geohash})</Popup>
						</Marker>
					) : null}
					{draftPickup && draftDrop ? (
						<Polyline positions={[draftPickup, draftDrop]} pathOptions={{ color: "#7b4dff", dashArray: "6 6", weight: 3 }} />
					) : null}

					{selectedRideRoute.length > 0 ? (
						<Polyline
							positions={selectedRideRoute}
							pathOptions={{ color: "#ff7a4f", weight: 4 }}
						/>
					) : null}
				</MapContainer>
			</section>

			<div className="grid-two">
				<section className="card">
					<h2>Available rides</h2>
					<div className="rides-list">
						{mappedRides.map(ride => (
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
								<a
									href={toGoogleDirectionsUrl(ride.start, ride.end)}
									target="_blank"
									rel="noreferrer"
									onClick={event => event.stopPropagation()}
								>
									Open Route In Google Maps
								</a>
							</button>
						))}
					</div>
				</section>

				<section className="card">
					<h2>Create ride</h2>
					<form className="form-card compact" onSubmit={handleCreateRide}>
						<div className="pick-mode">
							<button
								type="button"
								className={`btn ${ridePickTarget === "start" ? "primary" : "ghost"}`}
								onClick={() => {
									setActiveMapPicker("ride");
									setRidePickTarget("start");
								}}
							>
								Pick Start From Map
							</button>
							<button
								type="button"
								className={`btn ${ridePickTarget === "end" ? "primary" : "ghost"}`}
								onClick={() => {
									setActiveMapPicker("ride");
									setRidePickTarget("end");
								}}
							>
								Pick End From Map
							</button>
						</div>
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
						<div className="pick-mode">
							<button
								type="button"
								className={`btn ${bookingPickTarget === "pickup" && activeMapPicker === "booking" ? "primary" : "ghost"}`}
								onClick={() => {
									setActiveMapPicker("booking");
									setBookingPickTarget("pickup");
								}}
							>
								Pick Pickup From Map
							</button>
							<button
								type="button"
								className={`btn ${bookingPickTarget === "drop" && activeMapPicker === "booking" ? "primary" : "ghost"}`}
								onClick={() => {
									setActiveMapPicker("booking");
									setBookingPickTarget("drop");
								}}
							>
								Pick Drop From Map
							</button>
						</div>
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
