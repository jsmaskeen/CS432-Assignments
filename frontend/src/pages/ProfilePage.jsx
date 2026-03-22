import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";

export default function ProfilePage() {
	const [me, setMe] = useState(null);
	const [message, setMessage] = useState("");

	useEffect(() => {
		api
			.me()
			.then(data => setMe(data))
			.catch(error => setMessage(error.message));
	}, []);

	return (
		<div className="page">
			<section className="card">
				<h2>Profile</h2>
				{me ? (
					<ul className="booking-list">
						<li>
							<strong>{me.full_name || me.username}</strong>
							<span>Username: {me.username}</span>
							<span>Email: {me.email}</span>
							<span>Role: {me.role}</span>
						</li>
					</ul>
				) : (
					<p className="message">Loading profile...</p>
				)}
				<div className="chip-row" style={{ marginTop: 12 }}>
					<Link className="btn ghost" to="/preferences">
						Preferences
					</Link>
					<Link className="btn ghost" to="/reviews">
						Reviews
					</Link>
					<Link className="btn ghost" to="/settlements">
						Settlements
					</Link>
				</div>
			</section>
			<p className="message">{message}</p>
		</div>
	);
}
