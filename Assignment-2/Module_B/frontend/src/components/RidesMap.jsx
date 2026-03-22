import React from "react";
import L from "leaflet";
import {
	MapContainer,
	TileLayer,
	Marker,
	Polyline,
	Popup,
	useMap,
	useMapEvents,
} from "react-leaflet";

const selectedStartIcon = new L.Icon({
	iconUrl:
		"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
});

const bookingPickupIcon = new L.Icon({
	iconUrl:
		"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
});

const bookingDropIcon = new L.Icon({
	iconUrl:
		"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
});

const smallStartIcon = new L.Icon({
	iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [10, 15],
	iconAnchor: [9, 30],
	popupAnchor: [1, -24],
});

const endIcon = new L.Icon({
	iconUrl:
		"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
});

const smallEndIcon = new L.Icon({
	iconUrl:
		"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
	shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
	iconSize: [10, 15],
	iconAnchor: [9, 30],
	popupAnchor: [1, -24],
});

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

function Focus({ ride }) {
	const map = useMap();
	React.useEffect(() => {
		if (!ride || !Array.isArray(ride.start)) return;
		try {
			map.fitBounds(L.latLngBounds([ride.start, ride.end]), {
				padding: [50, 50],
				maxZoom: 13,
			});
		} catch {
			// Ignore fit errors.
		}
	}, [map, ride]);
	return null;
}

export default function RidesMap({
	selected,
	selectedId,
	mappedRides,
	bookingPickupPoint,
	bookingDropPoint,
	bookingLocations,
	bookingForm,
	bookingRoutePath,
	draftStart,
	draftEnd,
	rideLocations,
	rideForm,
	hostingRoute,
	selectedRoute,
	onMapPick,
}) {
	return (
		<div className="map-shell card panel map-stage">
			<div className="map-head">
				<h2>Map</h2>
				<p>Click a ride to focus the map.</p>
			</div>

			<MapContainer
				center={
					selected && Array.isArray(selected.start)
						? selected.start
						: [23.2156, 72.6369]
				}
				zoom={12}
				style={{ height: 520 }}
			>
				<TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
				<Focus ride={selected} />
				<MapClickCapture onPick={onMapPick} />
				{(mappedRides || []).map(ride => {
					const hasCoords = Array.isArray(ride.start) && Array.isArray(ride.end);
					return (
						<React.Fragment key={`m-${ride.RideID}`}>
							{hasCoords ? (
								<Polyline
									positions={[ride.start, ride.end]}
									pathOptions={{
										color:
											selectedId === ride.RideID ? "#ebbe0b" : "#8cbcff",
										weight: selectedId === ride.RideID ? 4 : 2,
										dashArray:
											selectedId === ride.RideID ? undefined : "8 10",
										opacity: selectedId === ride.RideID ? 0.95 : 0.55,
									}}
								/>
							) : null}
							{hasCoords ? (
								<Marker
									position={ride.start}
									icon={
										selectedId === ride.RideID
											? selectedStartIcon
											: smallStartIcon
									}
								>
									<Popup>Start (Ride #{ride.RideID})</Popup>
								</Marker>
							) : null}
							{hasCoords ? (
								<Marker
									position={ride.end}
									icon={selectedId === ride.RideID ? endIcon : smallEndIcon}
								>
									<Popup>End (Ride #{ride.RideID})</Popup>
								</Marker>
							) : null}
						</React.Fragment>
					);
				})}
				{bookingPickupPoint ? (
					<Marker position={bookingPickupPoint} icon={bookingPickupIcon}>
						<Popup>
							Booking pickup ({bookingLocations.pickup || bookingForm.pickup_geohash})
						</Popup>
					</Marker>
				) : null}
				{bookingDropPoint ? (
					<Marker position={bookingDropPoint} icon={bookingDropIcon}>
						<Popup>
							Booking drop ({bookingLocations.drop || bookingForm.drop_geohash})
						</Popup>
					</Marker>
				) : null}
				{bookingRoutePath.length > 0 ? (
					<Polyline
						positions={bookingRoutePath}
						pathOptions={{
							color: "#7b4dff",
							weight: 4,
							opacity: 0.9,
						}}
					/>
				) : bookingPickupPoint && bookingDropPoint ? (
					<Polyline
						positions={[bookingPickupPoint, bookingDropPoint]}
						pathOptions={{
							color: "#7b4dff",
							dashArray: "6 6",
							weight: 3,
							opacity: 0.85,
						}}
					/>
				) : null}
				{draftStart ? (
					<Marker position={draftStart} icon={selectedStartIcon}>
						<Popup>
							Host ride start ({rideLocations.start || rideForm.start_geohash})
						</Popup>
					</Marker>
				) : null}
				{draftEnd ? (
					<Marker position={draftEnd} icon={endIcon}>
						<Popup>
							Host ride end ({rideLocations.end || rideForm.end_geohash})
						</Popup>
					</Marker>
				) : null}
				{hostingRoute.length > 0 ? (
					<Polyline
						positions={hostingRoute}
						pathOptions={{ color: "#34a853", weight: 4, opacity: 0.95 }}
					/>
				) : draftStart && draftEnd ? (
					<Polyline
						positions={[draftStart, draftEnd]}
						pathOptions={{
							color: "#34a853",
							weight: 3,
							opacity: 0.4,
							dashArray: "6 6",
						}}
					/>
				) : null}
				{selectedRoute.length > 0 ? (
					<Polyline
						positions={selectedRoute}
						pathOptions={{ color: "#0beb87", weight: 5, opacity: 0.9 }}
					/>
				) : null}
			</MapContainer>
		</div>
	);
}
