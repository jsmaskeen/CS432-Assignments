import React, { useEffect, useState } from "react";

import { api } from "../api";

const defaultForm = {
	gender_preference: "Any",
	notify_on_new_ride: false,
	music_preference: "",
};

export default function PreferencesPage() {
	const [form, setForm] = useState(defaultForm);
	const [message, setMessage] = useState("");

	async function loadPreference() {
		try {
			const data = await api.myPreference();
			if (!data) {
				setMessage("No preference set yet.");
				return;
			}
			setForm({
				gender_preference: data.Gender_Preference,
				notify_on_new_ride: data.Notify_On_New_Ride,
				music_preference: data.Music_Preference || "",
			});
			setMessage("Preference loaded");
		} catch (error) {
			setMessage(error.message);
		}
	}

	useEffect(() => {
		loadPreference();
	}, []);

	async function handleSubmit(event) {
		event.preventDefault();
		setMessage("Saving preference...");
		try {
			await api.upsertPreference({
				...form,
				music_preference: form.music_preference || null,
			});
			setMessage("Preference saved");
		} catch (error) {
			setMessage(error.message);
		}
	}

	return (
		<div className="page auth-page">
			<form className="card form-card" onSubmit={handleSubmit}>
				<h2>My Preferences</h2>
				<label>
					Gender preference
					<select
						value={form.gender_preference}
						onChange={event =>
							setForm({ ...form, gender_preference: event.target.value })
						}
					>
						<option value="Any">Any</option>
						<option value="Same-Gender Only">Same-Gender Only</option>
					</select>
				</label>
				<label>
					<input
						type="checkbox"
						checked={form.notify_on_new_ride}
						onChange={event =>
							setForm({ ...form, notify_on_new_ride: event.target.checked })
						}
					/>
					Notify me on new rides
				</label>
				<input
					placeholder="Music preference (optional)"
					value={form.music_preference}
					onChange={event => setForm({ ...form, music_preference: event.target.value })}
				/>
				<button className="btn primary" type="submit">
					Save
				</button>
			</form>

			<p className="message">{message}</p>
		</div>
	);
}
