import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";

export default function SavedLocationsPage() {
	const [saved, setSaved] = useState([]);
	const [locations, setLocations] = useState([]);
	const [label, setLabel] = useState("");
	const [locationId, setLocationId] = useState("");
	const [message, setMessage] = useState("");

	const locationLookup = useMemo(() => {
		const map = new Map();
		locations.forEach(loc => map.set(loc.LocationID, loc));
		return map;
	}, [locations]);

	async function loadSavedAddresses() {
		try {
			const data = await api.listSavedAddresses();
			setSaved(data || []);
		} catch (error) {
			setMessage(error.message);
		}
	}

	async function loadLocations() {
		try {
			const data = await api.listLocations({ limit: 300 });
			setLocations(data || []);
		} catch (error) {
			setMessage(error.message);
		}
	}

	useEffect(() => {
		loadSavedAddresses();
		loadLocations();
	}, []);

	async function handleCreate(event) {
		event.preventDefault();
		setMessage("Saving...");
		try {
			await api.createSavedAddress({
				label: label.trim(),
				location_id: Number(locationId),
			});
			setLabel("");
			setLocationId("");
			setMessage("Saved address created");
			loadSavedAddresses();
		} catch (error) {
			setMessage(error.message);
		}
	}

	async function handleDelete(addressId) {
		try {
			await api.deleteSavedAddress(addressId);
			setMessage("Saved address deleted");
			loadSavedAddresses();
		} catch (error) {
			setMessage(error.message);
		}
	}

	return (
		<div className="page">
			<section className="card">
				<div className="section-title">
					<h2>Saved Locations</h2>
					<Link to="/locations" className="btn ghost">
						Go to Locations Page
					</Link>
				</div>
				<form className="form-card compact" onSubmit={handleCreate}>
					<input
						placeholder="Label (Home, Lab, Hostel)"
						value={label}
						onChange={event => setLabel(event.target.value)}
						required
					/>
					<select
						value={locationId}
						onChange={event => setLocationId(event.target.value)}
						required
					>
						<option value="">Select location</option>
						{locations.map(location => (
							<option key={location.LocationID} value={location.LocationID}>
								{location.Location_Name} ({location.Location_Type})
							</option>
						))}
					</select>
					<button className="btn primary" type="submit">
						Save
					</button>
				</form>
			</section>

			<section className="card">
				<h3>My saved locations</h3>
				<ul className="booking-list">
					{saved.map(address => {
						const loc = locationLookup.get(address.LocationID);
						return (
							<li key={address.AddressID}>
								<strong>{address.Label}</strong>
								<span>
									{loc ? loc.Location_Name : "Location"} (#{address.LocationID})
								</span>
								<button
									className="btn ghost"
									onClick={() => handleDelete(address.AddressID)}
									type="button"
								>
									Delete
								</button>
							</li>
						);
					})}
				</ul>
			</section>

			<p className="message">{message}</p>
		</div>
	);
}
