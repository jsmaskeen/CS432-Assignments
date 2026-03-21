import React, { useEffect, useState } from "react";

import { api } from "../api";

export default function SettlementsPage() {
	const [targetSettlementId, setTargetSettlementId] = useState("");
	const [paymentStatus, setPaymentStatus] = useState("Settled");
	const [settlements, setSettlements] = useState([]);
	const [message, setMessage] = useState("");

	async function loadSettlements() {
		try {
			const data = await api.mySettlements();
			setSettlements(data);
			setMessage(`Loaded ${data.length} settlements`);
		} catch (error) {
			setMessage(error.message);
		}
	}

	useEffect(() => {
		loadSettlements();
	}, []);

	async function handleUpdateStatus(event) {
		event.preventDefault();
		setMessage("Updating settlement status...");
		try {
			await api.updateSettlementStatus(Number(targetSettlementId), {
				payment_status: paymentStatus,
			});
			setTargetSettlementId("");
			setMessage("Settlement status updated");
			loadSettlements();
		} catch (error) {
			setMessage(error.message);
		}
	}

	return (
		<div className="page">
			<section className="card form-card compact">
				<h2>Update payment status</h2>
				<form onSubmit={handleUpdateStatus}>
					<input
						type="number"
						placeholder="Settlement ID"
						value={targetSettlementId}
						onChange={event => setTargetSettlementId(event.target.value)}
						required
					/>
					<select
						value={paymentStatus}
						onChange={event => setPaymentStatus(event.target.value)}
					>
						<option value="Unpaid">Unpaid</option>
						<option value="Settled">Settled</option>
					</select>
					<button className="btn primary" type="submit">
						Update
					</button>
				</form>
			</section>

			<section className="card">
				<h3>My settlements</h3>
				<ul className="booking-list">
					{settlements.map(settlement => (
						<li key={settlement.SettlementID}>
							<strong>Settlement #{settlement.SettlementID}</strong>
							<span>Booking #{settlement.BookingID}</span>
							<span>Cost: {settlement.Calculated_Cost}</span>
							<span>Status: {settlement.Payment_Status}</span>
						</li>
					))}
				</ul>
			</section>

			<p className="message">{message}</p>
		</div>
	);
}
