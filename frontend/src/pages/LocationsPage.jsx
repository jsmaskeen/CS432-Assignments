import React, { useEffect, useState } from "react";

import { api } from "../api";

export default function LocationsPage() {
	const [search, setSearch] = useState("");
	const [locationType, setLocationType] = useState("");
	const [locations, setLocations] = useState([]);
	const [message, setMessage] = useState("");

	async function loadLocations() {
		try {
			const data = await api.listLocations({ search, location_type: locationType });
			setLocations(data);
			setMessage(`Loaded ${data.length} locations`);
		} catch (error) {
			setMessage(error.message);
		}
	}

	useEffect(() => {
		loadLocations();
	}, []);

	return (
		<div className="page">
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
