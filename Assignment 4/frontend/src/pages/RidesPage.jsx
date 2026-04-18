import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import geohash from "ngeohash";
import { api } from "../api";
import RidesMap from "../components/RidesMap";

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
};


function decodeGeohash(geo) {
	try {
		const decoded = geohash.decode(geo);
		return [decoded.latitude, decoded.longitude];
	} catch {
		return null;
	}
}

async function fetchNominatimSuggestions(query, userLocation) {
	if (!query) {
		return [];
	}
	const params = new URLSearchParams({
		format: "json",
		limit: "5",
		q: query,
	});
	if (userLocation?.lat && userLocation?.lng) {
		const delta = 0.02;
		const left = userLocation.lng - delta;
		const right = userLocation.lng + delta;
		const top = userLocation.lat + delta;
		const bottom = userLocation.lat - delta;
		params.set("viewbox", `${left},${top},${right},${bottom}`);
		params.set("bounded", "0");
	}
	const url = `https://nominatim.openstreetmap.org/search?${params.toString()}`;
	const response = await fetch(url, {
		headers: {
			"Accept-Language": "en",
		},
	});
	if (!response.ok) {
		return [];
	}
	const data = await response.json();
	return (data || [])
		.map(item => {
			const lat = Number(item?.lat);
			const lng = Number(item?.lon);
			if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
				return null;
			}
			return {
				id: `nom-${item.place_id}`,
				label: item.display_name || query,
				geohash: geohash.encode(lat, lng, 7),
				source: "Nearby match",
			};
		})
		.filter(Boolean);
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
		return { coordinates: [], distanceMeters: null };
	}
	const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`;
	const response = await fetch(url);
	const data = await response.json();
	const route = data?.routes?.[0];
	return {
		coordinates: route?.geometry?.coordinates || [],
		distanceMeters: route?.distance,
	};
}

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


export default function RidesPage() {
	const [rides, setRides] = useState([]);
	const [selectedId, setSelectedId] = useState(null);
	const [selectedRoute, setSelectedRoute] = useState([]);
	const [confirmedStops, setConfirmedStops] = useState([]);
	const [sidebarMode, setSidebarMode] = useState("booking");
	const [rideForm, setRideForm] = useState(initialRide);
	const [rideLocations, setRideLocations] = useState({ start: "", end: "" });
	const [rideStartSuggestions, setRideStartSuggestions] = useState([]);
	const [rideEndSuggestions, setRideEndSuggestions] = useState([]);
	const [ridePickTarget, setRidePickTarget] = useState("start");
	const [hostingRoute, setHostingRoute] = useState([]);
	const [hostingRouteDistanceKm, setHostingRouteDistanceKm] = useState(null);
	const [hostingDistanceLoading, setHostingDistanceLoading] = useState(false);
	const [bookingForm, setBookingForm] = useState(initialBooking);
	const [bookingLocations, setBookingLocations] = useState({ pickup: "", drop: "" });
	const [bookingPickupSuggestions, setBookingPickupSuggestions] = useState([]);
	const [bookingDropSuggestions, setBookingDropSuggestions] = useState([]);
	const [bookingRouteDistanceKm, setBookingRouteDistanceKm] = useState(null);
	const [bookingRoutePath, setBookingRoutePath] = useState([]);
	const [bookingDistanceLoading, setBookingDistanceLoading] = useState(false);
	const [bookingPickTarget, setBookingPickTarget] = useState("pickup");
	const [rideStartSearchLoading, setRideStartSearchLoading] = useState(false);
	const [rideEndSearchLoading, setRideEndSearchLoading] = useState(false);
	const [bookingPickupSearchLoading, setBookingPickupSearchLoading] = useState(false);
	const [bookingDropSearchLoading, setBookingDropSearchLoading] = useState(false);
	const [locationPickerOpen, setLocationPickerOpen] = useState(false);
	const [locationPickTarget, setLocationPickTarget] = useState("pickup");
	const [locationSearch, setLocationSearch] = useState("");
	const [locationTypeFilter, setLocationTypeFilter] = useState("");
	const [locationOptions, setLocationOptions] = useState([]);
	const [locationLoading, setLocationLoading] = useState(false);
	const [locationsCatalog, setLocationsCatalog] = useState([]);
	const [activeMapPicker, setActiveMapPicker] = useState("booking");
	const [creatingRide, setCreatingRide] = useState(false);
	const [message, setMessage] = useState("");
	const [userLocation, setUserLocation] = useState(null);

	useEffect(() => {
		api.listRides()
			.then(r => setRides(r || []))
			.catch(() => setMessage("Failed to load rides"));
	}, []);

	useEffect(() => {
		let cancelled = false;
		if (!selectedId) {
			setConfirmedStops([]);
			return () => {};
		}

		api.listConfirmedBookingStops(selectedId)
			.then(data => {
				if (cancelled) {
					return;
				}
				const stops = (data || []).flatMap(booking => {
					const pickup = decodeGeohash(booking.Pickup_GeoHash);
					const drop = decodeGeohash(booking.Drop_GeoHash);
					return [pickup, drop].filter(Boolean);
				});
				setConfirmedStops(stops);
			})
			.catch(() => {
				if (!cancelled) {
					setConfirmedStops([]);
				}
			});

		return () => {
			cancelled = true;
		};
	}, [selectedId]);

	useEffect(() => {
		if (!navigator.geolocation) {
			return;
		}
		navigator.geolocation.getCurrentPosition(
			position => {
				setUserLocation({
					lat: position.coords.latitude,
					lng: position.coords.longitude,
				});
			},
			() => {
				// Ignore location errors; suggestions will still work without bias.
			},
			{ enableHighAccuracy: false, timeout: 8000 },
		);
	}, []);

	useEffect(() => {
		let cancelled = false;
		async function loadLocationsCatalog() {
			try {
				const data = await api.listLocations({ limit: 200 });
				if (!cancelled) {
					setLocationsCatalog(data || []);
				}
			} catch {
				if (!cancelled) {
					setLocationsCatalog([]);
				}
			}
		}

		loadLocationsCatalog();
		return () => {
			cancelled = true;
		};
	}, []);

	async function buildLocationSuggestions(query) {
		const trimmed = query.trim();
		if (!trimmed) {
			return [];
		}
		const lower = trimmed.toLowerCase();
		const savedMatches = (locationsCatalog || [])
			.filter(location => location.Location_Name?.toLowerCase().includes(lower))
			.slice(0, 5)
			.map(location => ({
				id: `saved-${location.LocationID}`,
				label: location.Location_Name,
				geohash: location.GeoHash,
				source: "Saved location",
			}));
		const nominatimMatches = await fetchNominatimSuggestions(trimmed, userLocation);
		const combined = [...savedMatches, ...nominatimMatches];
		const seen = new Set();
		return combined.filter(item => {
			if (!item?.geohash || seen.has(item.geohash)) {
				return false;
			}
			seen.add(item.geohash);
			return true;
		});
	}

	useEffect(() => {
		let cancelled = false;
		if (!rideLocations.start.trim()) {
			setRideStartSuggestions([]);
			setRideStartSearchLoading(false);
			return () => {};
		}
		setRideStartSearchLoading(true);
		const timer = setTimeout(async () => {
			const suggestions = await buildLocationSuggestions(rideLocations.start);
			if (!cancelled) {
				setRideStartSuggestions(suggestions);
				setRideStartSearchLoading(false);
			}
		}, 300);
		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	}, [rideLocations.start, locationsCatalog, userLocation]);

	useEffect(() => {
		let cancelled = false;
		if (!rideLocations.end.trim()) {
			setRideEndSuggestions([]);
			setRideEndSearchLoading(false);
			return () => {};
		}
		setRideEndSearchLoading(true);
		const timer = setTimeout(async () => {
			const suggestions = await buildLocationSuggestions(rideLocations.end);
			if (!cancelled) {
				setRideEndSuggestions(suggestions);
				setRideEndSearchLoading(false);
			}
		}, 300);
		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	}, [rideLocations.end, locationsCatalog, userLocation]);

	useEffect(() => {
		let cancelled = false;
		if (!bookingLocations.pickup.trim()) {
			setBookingPickupSuggestions([]);
			setBookingPickupSearchLoading(false);
			return () => {};
		}
		setBookingPickupSearchLoading(true);
		const timer = setTimeout(async () => {
			const suggestions = await buildLocationSuggestions(bookingLocations.pickup);
			if (!cancelled) {
				setBookingPickupSuggestions(suggestions);
				setBookingPickupSearchLoading(false);
			}
		}, 300);
		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	}, [bookingLocations.pickup, locationsCatalog, userLocation]);

	useEffect(() => {
		let cancelled = false;
		if (!bookingLocations.drop.trim()) {
			setBookingDropSuggestions([]);
			setBookingDropSearchLoading(false);
			return () => {};
		}
		setBookingDropSearchLoading(true);
		const timer = setTimeout(async () => {
			const suggestions = await buildLocationSuggestions(bookingLocations.drop);
			if (!cancelled) {
				setBookingDropSuggestions(suggestions);
				setBookingDropSearchLoading(false);
			}
		}, 300);
		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	}, [bookingLocations.drop, locationsCatalog, userLocation]);

	const mappedRides = rides
		.map(r => {
			const start = decodeGeohash(r.Start_GeoHash);
			const end = decodeGeohash(r.End_GeoHash);
			if (!start || !end) return null;
			return { ...r, start, end };
		})
		.filter(Boolean);

	const selected = mappedRides.find(r => r.RideID === selectedId) || null;
	const draftStart = decodeGeohash(rideForm.start_geohash);
	const draftEnd = decodeGeohash(rideForm.end_geohash);
	const bookingPickupPoint = decodeGeohash(bookingForm.pickup_geohash);
	const bookingDropPoint = decodeGeohash(bookingForm.drop_geohash);
	const orderedConfirmedStops = React.useMemo(() => {
		const startPoint = selected?.Start_GeoHash
			? decodeGeohash(selected.Start_GeoHash)
			: null;
		return orderStopsByDistance(startPoint, confirmedStops);
	}, [selected?.Start_GeoHash, confirmedStops]);

	useEffect(() => {
		async function loadSelectedRoute() {
			if (!selected) {
				setSelectedRoute([]);
				return;
			}

			try {
				const routeStops = [selected.start, ...orderedConfirmedStops, selected.end];
				const routeData = await fetchRouteData(routeStops);
				setSelectedRoute(routeData.coordinates.map(point => [point[1], point[0]]));
			} catch {
				setSelectedRoute([]);
			}
		}

		loadSelectedRoute();
	}, [selected?.Start_GeoHash, selected?.End_GeoHash, orderedConfirmedStops]);

	useEffect(() => {
		let cancelled = false;

		async function loadHostingRouteDistance() {
			const hostStart = decodeGeohash(rideForm.start_geohash);
			const hostEnd = decodeGeohash(rideForm.end_geohash);

			if (!hostStart || !hostEnd) {
				setHostingDistanceLoading(false);
				setHostingRouteDistanceKm(null);
				setHostingRoute([]);
				return;
			}
			if (rideForm.start_geohash === rideForm.end_geohash) {
				setHostingDistanceLoading(false);
				setHostingRouteDistanceKm(null);
				setHostingRoute([]);
				return;
			}

			setHostingDistanceLoading(true);
			try {
				const routeData = await fetchRouteData([hostStart, hostEnd]);
				if (cancelled) {
					return;
				}
				const points = routeData.coordinates || [];
				setHostingRoute(points.map(point => [point[1], point[0]]));

				if (typeof routeData.distanceMeters === "number") {
					setHostingRouteDistanceKm(Number((routeData.distanceMeters / 1000).toFixed(2)));
				} else {
					setHostingRouteDistanceKm(null);
				}
			} catch {
				if (!cancelled) {
					setHostingRouteDistanceKm(null);
					setHostingRoute([]);
				}
			} finally {
				if (!cancelled) {
					setHostingDistanceLoading(false);
				}
			}
		}

		const timer = setTimeout(loadHostingRouteDistance, 250);
		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	}, [rideForm.start_geohash, rideForm.end_geohash]);

	useEffect(() => {
		let cancelled = false;

		async function loadBookingRouteDistance() {
			if (!bookingPickupPoint || !bookingDropPoint) {
				setBookingDistanceLoading(false);
				setBookingRouteDistanceKm(null);
				return;
			}
			if (bookingForm.pickup_geohash === bookingForm.drop_geohash) {
				setBookingDistanceLoading(false);
				setBookingRouteDistanceKm(null);
				return;
			}

			setBookingDistanceLoading(true);
			try {
				const routeData = await fetchRouteData([
					bookingPickupPoint,
					bookingDropPoint,
				]);
				const distanceMeters = routeData.distanceMeters;
				if (cancelled || typeof distanceMeters !== "number") {
					return;
				}

				const km = Number((distanceMeters / 1000).toFixed(2));
				setBookingRouteDistanceKm(km);
			} catch {
				if (!cancelled) {
					setBookingRouteDistanceKm(null);
				}
			} finally {
				if (!cancelled) {
					setBookingDistanceLoading(false);
				}
			}
		}

		const timer = setTimeout(loadBookingRouteDistance, 250);
		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	}, [bookingForm.pickup_geohash, bookingForm.drop_geohash]);

	useEffect(() => {
		let cancelled = false;

		async function loadBookingRoutePath() {
			if (!selected || !bookingPickupPoint || !bookingDropPoint) {
				setBookingRoutePath([]);
				return;
			}
			setBookingRoutePath([]);
			const allStops = [
				...confirmedStops,
				bookingPickupPoint,
				bookingDropPoint,
			];
			const orderedStops = orderStopsByDistance(selected.start, allStops);
			const points = [selected.start, ...orderedStops, selected.end];
			try {
				const routeData = await fetchRouteData(points);
				if (cancelled) {
					return;
				}
				setBookingRoutePath(routeData.coordinates.map(point => [point[1], point[0]]));
			} catch {
				if (!cancelled) {
					setBookingRoutePath([]);
				}
			}
		}

		const timer = setTimeout(loadBookingRoutePath, 250);
		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	}, [
		selected?.RideID,
		bookingForm.pickup_geohash,
		bookingForm.drop_geohash,
		orderedConfirmedStops,
	]);

	async function handleBookRide(event) {
		event.preventDefault();
		if (!selectedId) {
			setMessage("Select a ride first");
			return;
		}
		if (!bookingForm.pickup_geohash || !bookingForm.drop_geohash) {
			setMessage("Select pickup and drop from the suggestions or map first.");
			return;
		}
		try {
			await api.bookRide(selectedId, {
				...bookingForm,
			});
			setMessage(`Ride #${selectedId} booked successfully`);
			setBookingForm(initialBooking);
			setBookingLocations({ pickup: "", drop: "" });
			const refreshed = await api.listRides();
			setRides(refreshed || []);
		} catch (error) {
			setMessage(error.message || "Booking failed");
		}
	}

	async function handleCreateRide(event) {
		event.preventDefault();
		if (creatingRide) {
			return;
		}
		if (!rideForm.start_geohash || !rideForm.end_geohash) {
			setMessage("Select start and end from the suggestions or map first.");
			return;
		}
		if (hostingRouteDistanceKm === null || hostingDistanceLoading) {
			setMessage(
				"Waiting for host route details from map API. Please try again in a moment.",
			);
			return;
		}
		setCreatingRide(true);
		setMessage("Creating ride...");
		try {
			await api.createRide({
				...rideForm,
				base_fare_per_km: Number(rideForm.base_fare_per_km),
				max_capacity: Number(rideForm.max_capacity),
			});
			setRideForm(initialRide);
			setRideLocations({ start: "", end: "" });
			setHostingRoute([]);
			setHostingRouteDistanceKm(null);
			setSidebarMode("booking");
			setMessage("Ride created");
			const refreshed = await api.listRides();
			setRides(refreshed || []);
		} catch (error) {
			setMessage(error.message || "Ride creation failed");
		} finally {
			setCreatingRide(false);
		}
	}

	function handleMapPick(latlng) {
		const hash = geohash.encode(latlng.lat, latlng.lng, 7);
		const label = `Map selection (${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)})`;

		if (activeMapPicker === "ride") {
			if (!ridePickTarget) {
				return;
			}
			if (ridePickTarget === "start") {
				setRideForm(prev => ({ ...prev, start_geohash: hash }));
				setRideLocations(prev => ({ ...prev, start: label }));
				setRidePickTarget("end");
				setMessage(`Picked ride start geohash: ${hash}`);
				return;
			}

			setRideForm(prev => ({ ...prev, end_geohash: hash }));
			setRideLocations(prev => ({ ...prev, end: label }));
			setMessage(`Picked ride end geohash: ${hash}`);
			return;
		}

		if (!bookingPickTarget) {
			return;
		}

		if (bookingPickTarget === "pickup") {
			setBookingForm(prev => ({ ...prev, pickup_geohash: hash }));
			setBookingLocations(prev => ({ ...prev, pickup: label }));
			setBookingPickTarget("drop");
			setMessage(`Picked pickup geohash: ${hash}`);
			return;
		}

		setBookingForm(prev => ({ ...prev, drop_geohash: hash }));
		setBookingLocations(prev => ({ ...prev, drop: label }));
		setMessage(`Picked drop geohash: ${hash}`);
	}

	function applySuggestionToBooking(target, suggestion) {
		if (!suggestion?.geohash) {
			setMessage("Selected suggestion has no geohash.");
			return;
		}
		if (target === "pickup") {
			setBookingForm(prev => ({ ...prev, pickup_geohash: suggestion.geohash }));
			setBookingLocations(prev => ({ ...prev, pickup: suggestion.label }));
			setBookingPickupSuggestions([]);
			setMessage(`Pickup set: ${suggestion.label}`);
			return;
		}
		setBookingForm(prev => ({ ...prev, drop_geohash: suggestion.geohash }));
		setBookingLocations(prev => ({ ...prev, drop: suggestion.label }));
		setBookingDropSuggestions([]);
		setMessage(`Drop set: ${suggestion.label}`);
	}

	function applySuggestionToRide(target, suggestion) {
		if (!suggestion?.geohash) {
			setMessage("Selected suggestion has no geohash.");
			return;
		}
		if (target === "start") {
			setRideForm(prev => ({ ...prev, start_geohash: suggestion.geohash }));
			setRideLocations(prev => ({ ...prev, start: suggestion.label }));
			setRideStartSuggestions([]);
			setMessage(`Start set: ${suggestion.label}`);
			return;
		}
		setRideForm(prev => ({ ...prev, end_geohash: suggestion.geohash }));
		setRideLocations(prev => ({ ...prev, end: suggestion.label }));
		setRideEndSuggestions([]);
		setMessage(`End set: ${suggestion.label}`);
	}

	async function loadLocationOptions(
		searchValue = locationSearch,
		typeValue = locationTypeFilter,
	) {
		setLocationLoading(true);
		try {
			const data = await api.listLocations({ search: searchValue, location_type: typeValue });
			setLocationOptions(data || []);
		} catch (error) {
			setMessage(error.message || "Failed to load locations");
		} finally {
			setLocationLoading(false);
		}
	}

	function openLocationPicker(target) {
		setLocationPickTarget(target);
		setLocationPickerOpen(true);
		setLocationSearch("");
		setLocationTypeFilter("");
		loadLocationOptions("", "");
	}

	function applyLocationGeohash(location) {
		if (!location?.GeoHash) {
			setMessage("Selected location has no geohash.");
			return;
		}

		if (locationPickTarget === "pickup") {
			setBookingForm(prev => ({ ...prev, pickup_geohash: location.GeoHash }));
			setBookingLocations(prev => ({ ...prev, pickup: location.Location_Name || "" }));
			setMessage(`Pickup set from location: ${location.Location_Name}`);
		} else {
			setBookingForm(prev => ({ ...prev, drop_geohash: location.GeoHash }));
			setBookingLocations(prev => ({ ...prev, drop: location.Location_Name || "" }));
			setMessage(`Drop set from location: ${location.Location_Name}`);
		}

		setLocationPickerOpen(false);
	}

	return (
		<div className="page rides-page">
			<div className="panel panel-strong">
				<div className="section-title">
					<div>
						<p className="eyebrow">Book & host</p>
						<h2>Live rides</h2>
					</div>
					<div className="chip-row">
						<Link to="/" className="btn ghost">
							Home
						</Link>
						<Link to="/auth" className="btn primary">
							Login / Switch
						</Link>
					</div>
				</div>
			</div>

			<div className="rides-layout">
				<div className="stack">
					<section className="card panel">
						<div className="section-title">
							<h3>Available rides</h3>
							<span className="pill">{rides.length}</span>
						</div>
						<div className="chip-row" style={{ marginBottom: 12 }}>
							<button
								type="button"
								className={`btn ${sidebarMode === "booking" ? "primary" : "ghost"}`}
								onClick={() => {
									setSidebarMode("booking");
									setActiveMapPicker("booking");
								}}
							>
								Booking
							</button>
							<button
								type="button"
								className={`btn ${sidebarMode === "hosting" ? "primary" : "ghost"}`}
								onClick={() => {
									setSidebarMode("hosting");
									setActiveMapPicker("ride");
								}}
							>
								Hosting
							</button>
						</div>
						<div className="rides-list">
							{mappedRides.map(r => (
								<button
									key={r.RideID}
									className={`ride-card ${selectedId === r.RideID ? "selected" : ""}`}
									onClick={() => {
										setSelectedId(r.RideID);
										setBookingForm(prev => ({
											...prev,
											pickup_geohash: r.Start_GeoHash || prev.pickup_geohash,
											drop_geohash: r.End_GeoHash || prev.drop_geohash,
										}));
										setBookingLocations(prev => ({
											...prev,
											pickup: "Ride start",
											drop: "Ride end",
										}));
									}}
								>
									<div className="section-title">
										<strong>Ride #{r.RideID}</strong>
										<span className="pill">{r.Vehicle_Type || "—"}</span>
									</div>
									<div className="chip-row">
										<span className="pill success">
											Seats {r.Available_Seats}/{r.Max_Capacity}
										</span>
										<span className="pill">₹{r.Base_Fare_Per_KM} per km</span>
									</div>
									<div className="list-inline">
										<span>{r.Start_GeoHash || "—"}</span>
										<span>→</span>
										<span>{r.End_GeoHash || "—"}</span>
									</div>
								</button>
							))}
						</div>
					</section>

					{sidebarMode === "booking" && selected ? (
						<section className="card panel">
							<div className="section-title">
								<h3>Book selected ride</h3>
								<span className="pill success">Ride #{selected.RideID}</span>
							</div>
							<form className="form-card compact" onSubmit={handleBookRide}>
								<div className="chip-row">
									<button
										type="button"
										className="btn ghost"
										onClick={() => {
											setActiveMapPicker("booking");
											setBookingPickTarget(prev => (prev === "pickup" ? "drop" : "pickup"));
										}}
									>
										Select {bookingPickTarget === "pickup" ? "pickup" : "drop"} from map
									</button>
								</div>
								<p className="message">
									Next map pick: {bookingPickTarget === "pickup" ? "Pickup" : "Drop"}
								</p>
								<input
									placeholder="Pickup location"
									value={bookingLocations.pickup}
									onChange={event => {
										setBookingLocations({
											...bookingLocations,
											pickup: event.target.value,
										});
										setBookingForm(prev => ({ ...prev, pickup_geohash: "" }));
									}}
									required
								/>
								{bookingPickupSearchLoading ? (
									<p className="message">Searching locations...</p>
								) : null}
								{bookingPickupSuggestions.length > 0 ? (
									<ul className="booking-list">
										{bookingPickupSuggestions.map(suggestion => (
											<li key={`pickup-${suggestion.id}`}>
												<button
													type="button"
													className="btn ghost"
													onClick={() =>
														applySuggestionToBooking("pickup", suggestion)
													}
												>
													{suggestion.label}
												</button>
												<span className="small">{suggestion.source}</span>
											</li>
										))}
									</ul>
								) : null}
								<p className="message">
									Pickup geohash: {bookingForm.pickup_geohash || "-"}
								</p>
								<input
									placeholder="Drop location"
									value={bookingLocations.drop}
									onChange={event => {
										setBookingLocations({
											...bookingLocations,
											drop: event.target.value,
										});
										setBookingForm(prev => ({ ...prev, drop_geohash: "" }));
									}}
									required
								/>
								{bookingDropSearchLoading ? (
									<p className="message">Searching locations...</p>
								) : null}
								{bookingDropSuggestions.length > 0 ? (
									<ul className="booking-list">
										{bookingDropSuggestions.map(suggestion => (
											<li key={`drop-${suggestion.id}`}>
												<button
													type="button"
													className="btn ghost"
													onClick={() => applySuggestionToBooking("drop", suggestion)}
												>
													{suggestion.label}
												</button>
												<span className="small">{suggestion.source}</span>
											</li>
										))}
									</ul>
								) : null}
								<p className="message">
									Drop geohash: {bookingForm.drop_geohash || "-"}
								</p>
								<p className="message">
									{bookingDistanceLoading
										? "Calculating route distance..."
										: bookingRouteDistanceKm
											? `Route distance (OSRM): ${bookingRouteDistanceKm} km`
											: "Route distance (OSRM): -"}
								</p>
								<button className="btn primary" type="submit">
									Confirm Booking
								</button>
							</form>
						</section>
					) : null}

					{sidebarMode === "hosting" ? (
						<section className="card panel">
							<div className="section-title">
								<h3>Host a ride</h3>
								<span className="pill">New</span>
							</div>
							<form className="form-card compact" onSubmit={handleCreateRide}>
								<div className="chip-row">
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
									placeholder="Start location"
									value={rideLocations.start}
									onChange={event => {
										setRideLocations({
											...rideLocations,
											start: event.target.value,
										});
										setRideForm(prev => ({ ...prev, start_geohash: "" }));
									}}
									required
								/>
								{rideStartSearchLoading ? (
									<p className="message">Searching locations...</p>
								) : null}
								{rideStartSuggestions.length > 0 ? (
									<ul className="booking-list">
										{rideStartSuggestions.map(suggestion => (
											<li key={`start-${suggestion.id}`}>
												<button
													type="button"
													className="btn ghost"
													onClick={() => applySuggestionToRide("start", suggestion)}
												>
													{suggestion.label}
												</button>
												<span className="small">{suggestion.source}</span>
											</li>
										))}
									</ul>
								) : null}
								<p className="message">
									Start geohash: {rideForm.start_geohash || "-"}
								</p>
								<input
									placeholder="End location"
									value={rideLocations.end}
									onChange={event => {
										setRideLocations({
											...rideLocations,
											end: event.target.value,
										});
										setRideForm(prev => ({ ...prev, end_geohash: "" }));
									}}
									required
								/>
								{rideEndSearchLoading ? (
									<p className="message">Searching locations...</p>
								) : null}
								{rideEndSuggestions.length > 0 ? (
									<ul className="booking-list">
										{rideEndSuggestions.map(suggestion => (
											<li key={`end-${suggestion.id}`}>
												<button
													type="button"
													className="btn ghost"
													onClick={() => applySuggestionToRide("end", suggestion)}
												>
													{suggestion.label}
												</button>
												<span className="small">{suggestion.source}</span>
											</li>
										))}
									</ul>
								) : null}
								<p className="message">
									End geohash: {rideForm.end_geohash || "-"}
								</p>
								<input
									type="datetime-local"
									value={rideForm.departure_time}
									onChange={event =>
										setRideForm({
											...rideForm,
											departure_time: event.target.value,
										})
									}
									required
								/>
								<input
									placeholder="Vehicle type"
									value={rideForm.vehicle_type}
									onChange={event =>
										setRideForm({
											...rideForm,
											vehicle_type: event.target.value,
										})
									}
									required
								/>
								<input
									type="number"
									min="1"
									max="10"
									placeholder="Max capacity"
									value={rideForm.max_capacity}
									onChange={event =>
										setRideForm({
											...rideForm,
											max_capacity: event.target.value,
										})
									}
									required
								/>
								<input
									type="number"
									min="1"
									step="0.01"
									placeholder="Fare per km"
									value={rideForm.base_fare_per_km}
									onChange={event =>
										setRideForm({
											...rideForm,
											base_fare_per_km: event.target.value,
										})
									}
									required
								/>
								<p className="message">
									{hostingDistanceLoading
										? "Calculating host route distance..."
										: hostingRouteDistanceKm
											? `Host route distance (OSRM): ${hostingRouteDistanceKm} km`
											: "Host route distance (OSRM): -"}
								</p>
								<button className="btn primary" type="submit" disabled={creatingRide || hostingDistanceLoading}>
									{creatingRide ? "Publishing..." : "Publish Ride"}
								</button>
							</form>
						</section>
					) : null}
				</div>

				<RidesMap
					selected={selected}
					selectedId={selectedId}
					mappedRides={mappedRides}
					bookingPickupPoint={bookingPickupPoint}
					bookingDropPoint={bookingDropPoint}
					bookingLocations={bookingLocations}
					bookingForm={bookingForm}
					bookingRoutePath={bookingRoutePath}
					draftStart={draftStart}
					draftEnd={draftEnd}
					rideLocations={rideLocations}
					rideForm={rideForm}
					hostingRoute={hostingRoute}
					selectedRoute={selectedRoute}
					onMapPick={handleMapPick}
				/>
			</div>

			{locationPickerOpen ? (
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
							width: "min(780px, 94vw)",
							maxHeight: "80vh",
							overflow: "auto",
							background: "rgba(0, 0, 0, 0.95)",
						}}
					>
						<div className="section-title" style={{ marginBottom: 10 }}>
							<h3>
								Pick {locationPickTarget === "pickup" ? "Pickup" : "Drop"} From
								Locations
							</h3>
							<button
								className="btn ghost"
								type="button"
								onClick={() => setLocationPickerOpen(false)}
							>
								Close
							</button>
						</div>
						<form
							className="form-card compact"
							onSubmit={event => {
								event.preventDefault();
								loadLocationOptions();
							}}
						>
							<input
								placeholder="Search by name"
								value={locationSearch}
								onChange={event => setLocationSearch(event.target.value)}
							/>
							<input
								placeholder="Location type (Campus, City, Transport...)"
								value={locationTypeFilter}
								onChange={event => setLocationTypeFilter(event.target.value)}
							/>
							<button type="submit" className="btn primary">
								Search
							</button>
						</form>
						<ul className="booking-list" style={{ marginTop: 10 }}>
							{locationLoading ? <li>Loading locations...</li> : null}
							{!locationLoading && locationOptions.length === 0 ? (
								<li>No locations found.</li>
							) : null}
							{locationOptions.map(location => (
								<li key={location.LocationID}>
									<strong>{location.Location_Name}</strong>
									<span>Type: {location.Location_Type}</span>
									<span>GeoHash: {location.GeoHash || "-"}</span>
									<button
										type="button"
										className="btn primary"
										onClick={() => applyLocationGeohash(location)}
										disabled={!location.GeoHash}
									>
										Use This Location
									</button>
								</li>
							))}
						</ul>
					</section>
				</div>
			) : null}

			<p className="message">{message}</p>
		</div>
	);
}