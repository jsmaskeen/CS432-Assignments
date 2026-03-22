import React, { useEffect, useMemo, useRef, useState } from "react";
import geohash from "ngeohash";
import { MapContainer, TileLayer, CircleMarker, useMap, useMapEvents } from "react-leaflet";

import { api } from "../api";

const initialCreateForm = {
	location_name: "",
	location_type: "Campus",
	geohash: "",
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

function MapClickCapture({ onPick }) {
	useMapEvents({
		click(event) {
			if (onPick) {
				onPick(event.latlng);
			}
		},
	});

	return null;
}

function MapViewportController({ target }) {
	const map = useMap();
	const lastTargetRef = useRef(null);

	useEffect(() => {
		if (!target || target.length !== 2) {
			return;
		}

		const [lat, lng] = target;
		if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
			return;
		}

		const nextKey = `${lat.toFixed(5)}:${lng.toFixed(5)}`;
		if (lastTargetRef.current === nextKey) {
			return;
		}

		lastTargetRef.current = nextKey;
		const nextZoom = Math.max(map.getZoom(), 13);
		map.flyTo([lat, lng], nextZoom, { duration: 0.55 });
	}, [map, target]);

	return null;
}

export default function LocationsPage() {
	const [search, setSearch] = useState("");
	const [locationType, setLocationType] = useState("");
	const [locations, setLocations] = useState([]);
	const [locationsCatalog, setLocationsCatalog] = useState([]);
	const [createForm, setCreateForm] = useState(initialCreateForm);
	const [createSearch, setCreateSearch] = useState("");
	const [createSuggestions, setCreateSuggestions] = useState([]);
	const [createSearchLoading, setCreateSearchLoading] = useState(false);
	const [userLocation, setUserLocation] = useState(null);
	const [message, setMessage] = useState("");

	const pickedPoint = useMemo(() => decodeGeohash(createForm.geohash), [createForm.geohash]);
	const mapTargetPoint = useMemo(() => {
		if (pickedPoint) {
			return pickedPoint;
		}

		const typedGeohashPoint = decodeGeohash(createSearch.trim());
		if (typedGeohashPoint) {
			return typedGeohashPoint;
		}

		const topSuggestionGeohash = createSuggestions?.[0]?.geohash;
		const topSuggestionPoint = topSuggestionGeohash
			? decodeGeohash(topSuggestionGeohash)
			: null;
		if (topSuggestionPoint) {
			return topSuggestionPoint;
		}

		return [23.2156, 72.6369];
	}, [pickedPoint, createSearch, createSuggestions]);

	async function loadLocations() {
		try {
			const data = await api.listLocations({ search, location_type: locationType });
			setLocations(data);
			setLocationsCatalog(data || []);
			setMessage(`Loaded ${data.length} locations`);
		} catch (error) {
			setMessage(error.message);
		}
	}

	async function loadLocationsCatalog() {
		try {
			const data = await api.listLocations({ limit: 300 });
			setLocationsCatalog(data || []);
		} catch {
			setLocationsCatalog([]);
		}
	}

	async function buildLocationSuggestions(query) {
		const trimmed = query.trim();
		if (!trimmed) {
			return [];
		}
		const lower = trimmed.toLowerCase();
		const existingMatches = (locationsCatalog || [])
			.filter(location => location.Location_Name?.toLowerCase().includes(lower))
			.slice(0, 5)
			.map(location => ({
				id: `existing-${location.LocationID}`,
				label: location.Location_Name,
				geohash: location.GeoHash,
				locationType: location.Location_Type,
				source: "Existing location",
			}));
		const nominatimMatches = await fetchNominatimSuggestions(trimmed, userLocation);
		const combined = [...existingMatches, ...nominatimMatches];
		const seen = new Set();
		return combined.filter(item => {
			if (!item?.geohash || seen.has(item.geohash)) {
				return false;
			}
			seen.add(item.geohash);
			return true;
		});
	}

	function applySuggestion(suggestion) {
		if (!suggestion?.geohash) {
			setMessage("Selected suggestion has no geohash.");
			return;
		}
		setCreateForm(prev => ({
			...prev,
			location_name: prev.location_name || suggestion.label,
			location_type: suggestion.locationType || prev.location_type,
			geohash: suggestion.geohash,
		}));
		setCreateSuggestions([]);
		setMessage(`Geohash selected from ${suggestion.source}: ${suggestion.geohash}`);
	}

	function handleMapPick(latlng) {
		const hash = geohash.encode(latlng.lat, latlng.lng, 7);
		setCreateForm(prev => ({ ...prev, geohash: hash }));
		setMessage(`Picked geohash from map: ${hash}`);
	}

	async function handleCreateLocation(event) {
		event.preventDefault();
		if (!createForm.location_name.trim() || !createForm.location_type.trim()) {
			setMessage("Location name and type are required.");
			return;
		}
		setMessage("Creating location...");
		try {
			await api.createLocation({
				location_name: createForm.location_name.trim(),
				location_type: createForm.location_type.trim(),
				geohash: createForm.geohash.trim() || null,
			});
			setCreateForm(initialCreateForm);
			setCreateSearch("");
			setCreateSuggestions([]);
			await loadLocations();
			await loadLocationsCatalog();
			setMessage("Location created successfully");
		} catch (error) {
			setMessage(error.message || "Failed to create location");
		}
	}

	useEffect(() => {
		loadLocations();
		loadLocationsCatalog();
	}, []);

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
				// Ignore location errors; suggestions still work.
			},
			{ enableHighAccuracy: false, timeout: 8000 },
		);
	}, []);

	useEffect(() => {
		let cancelled = false;
		if (!createSearch.trim()) {
			setCreateSuggestions([]);
			setCreateSearchLoading(false);
			return () => {};
		}
		setCreateSearchLoading(true);
		const timer = setTimeout(async () => {
			const suggestions = await buildLocationSuggestions(createSearch);
			if (!cancelled) {
				setCreateSuggestions(suggestions);
				setCreateSearchLoading(false);
			}
		}, 300);
		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	}, [createSearch, locationsCatalog, userLocation]);

	return (
		<div className="page">
			<section className="card">
				<h2>Add New Location</h2>
				<form className="form-card compact" onSubmit={handleCreateLocation}>
					<input
						placeholder="Location name"
						value={createForm.location_name}
						onChange={event =>
							setCreateForm(prev => ({ ...prev, location_name: event.target.value }))
						}
						required
					/>
					<input
						placeholder="Location type (Campus, City, Transport...)"
						value={createForm.location_type}
						onChange={event =>
							setCreateForm(prev => ({ ...prev, location_type: event.target.value }))
						}
						required
					/>
					<input
						placeholder="Find area to pick geohash (suggestions)"
						value={createSearch}
						onChange={event => setCreateSearch(event.target.value)}
					/>
					{createSearchLoading ? (
						<p className="message">Searching suggestions...</p>
					) : null}
					{createSuggestions.length > 0 ? (
						<ul className="booking-list">
							{createSuggestions.map(suggestion => (
								<li key={suggestion.id}>
									<button
										type="button"
										className="btn ghost"
										onClick={() => applySuggestion(suggestion)}
									>
										{suggestion.label}
									</button>
									<span className="small">{suggestion.source}</span>
								</li>
							))}
						</ul>
					) : null}
					<input
						placeholder="GeoHash (map click or suggestion)"
						value={createForm.geohash}
						onChange={event =>
							setCreateForm(prev => ({ ...prev, geohash: event.target.value }))
						}
					/>
					<button type="submit" className="btn primary">
						Create Location
					</button>
				</form>

				<div style={{ marginTop: 12 }}>
					<p className="message">Click map to set geohash</p>
					<MapContainer
						center={mapTargetPoint}
						zoom={12}
						style={{ height: 300, borderRadius: 12, overflow: "hidden" }}
					>
						<TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
						<MapViewportController target={mapTargetPoint} />
						<MapClickCapture onPick={handleMapPick} />
						{mapTargetPoint ? (
							<CircleMarker
								center={mapTargetPoint}
								radius={8}
								pathOptions={{ color: pickedPoint ? "#0beb87" : "#65a4ff" }}
							/>
						) : null}
					</MapContainer>
				</div>
			</section>

			<section className="card">
				<h2>Locations</h2>
				<form
					className="form-card compact"
					onSubmit={event => {
						event.preventDefault();
						loadLocations();
					}}
				>
					<input
						placeholder="Search by name"
						value={search}
						onChange={event => setSearch(event.target.value)}
					/>
					<input
						placeholder="Location type (Campus, City, Transport...)"
						value={locationType}
						onChange={event => setLocationType(event.target.value)}
					/>
					<button type="submit" className="btn primary">
						Search
					</button>
				</form>
			</section>

			<section className="card">
				<h3>Results</h3>
				<ul className="booking-list">
					{locations.map(location => (
						<li key={location.LocationID}>
							<strong>{location.Location_Name}</strong>
							<span>Type: {location.Location_Type}</span>
							<span>GeoHash: {location.GeoHash || "-"}</span>
						</li>
					))}
				</ul>
			</section>

			<p className="message">{message}</p>
		</div>
	);
}
