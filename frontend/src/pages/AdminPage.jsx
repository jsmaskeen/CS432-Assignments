import React, { useEffect, useState } from "react";

import { api } from "../api";

export default function AdminPage() {
	const [currentUser, setCurrentUser] = useState(null);
	const [members, setMembers] = useState([]);
	const [rideStats, setRideStats] = useState(null);
	const [auditLogs, setAuditLogs] = useState([]);
	const [auditLimit, setAuditLimit] = useState(200);
	const [unauthorizedChanges, setUnauthorizedChanges] = useState([]);
	const [unauthorizedSummary, setUnauthorizedSummary] = useState([]);
	const [unauthorizedLimit, setUnauthorizedLimit] = useState(200);
	const [message, setMessage] = useState("");

	async function loadAdminData(
		auditLimitValue = auditLimit,
		unauthorizedLimitValue = unauthorizedLimit,
	) {
		setMessage("Loading admin data...");
		try {
			const [
				meData,
				membersData,
				statsData,
				logsData,
				unauthorizedRows,
				unauthorizedSummaryRows,
			] = await Promise.all([
				api.me(),
				api.listMembersAdmin(),
				api.getRideStatsAdmin(),
				api.listAuditLogsAdmin(auditLimitValue),
				api.listUnauthorizedDbChangesAdmin(unauthorizedLimitValue),
				api.listUnauthorizedDbSummaryAdmin(),
			]);
			setCurrentUser(meData);
			setMembers(membersData);
			setRideStats(statsData);
			setAuditLogs(logsData);
			setUnauthorizedChanges(unauthorizedRows);
			setUnauthorizedSummary(unauthorizedSummaryRows);
			setMessage(
				`Loaded ${membersData.length} members, ${logsData.length} audit logs, ${unauthorizedRows.length} unauthorized DB changes`,
			);
		} catch (error) {
			setMessage(error.message);
		}
	}

	useEffect(() => {
		loadAdminData();
	}, []);

	async function updateRole(memberId, nextRole) {
		try {
			await api.updateMemberRoleAdmin(memberId, nextRole);
			setMessage(`Updated member ${memberId} to ${nextRole}`);
			loadAdminData();
		} catch (error) {
			setMessage(error.message);
		}
	}

	if (currentUser && currentUser.role !== "admin") {
		return (
			<div className="page">
				<section className="card">
					<h2>Admin</h2>
					<p>Admin role required.</p>
				</section>
			</div>
		);
	}

	return (
		<div className="page">
			{rideStats ? (
				<section className="card">
					<h2>Ride Stats</h2>
					<div className="grid-two">
						<ul className="booking-list">
							<li>
								<strong>Total members</strong>
								<span>{rideStats.total_members}</span>
							</li>
							<li>
								<strong>Total rides</strong>
								<span>{rideStats.total_rides}</span>
							</li>
							<li>
								<strong>Open / Full / Cancelled / Completed</strong>
								<span>
									{rideStats.open_rides} / {rideStats.full_rides} /{" "}
									{rideStats.cancelled_rides} / {rideStats.completed_rides}
								</span>
							</li>
							<li>
								<strong>Total bookings</strong>
								<span>{rideStats.total_bookings}</span>
							</li>
						</ul>
						<ul className="booking-list">
							<li>
								<strong>Pending / Confirmed / Rejected / Cancelled bookings</strong>
								<span>
									{rideStats.pending_bookings} / {rideStats.confirmed_bookings} /{" "}
									{rideStats.rejected_bookings} / {rideStats.cancelled_bookings}
								</span>
							</li>
							<li>
								<strong>Total capacity seats</strong>
								<span>{rideStats.total_capacity_seats}</span>
							</li>
							<li>
								<strong>Total available seats</strong>
								<span>{rideStats.total_available_seats}</span>
							</li>
							<li>
								<strong>Total booked seats</strong>
								<span>{rideStats.total_booked_seats}</span>
							</li>
							<li>
								<strong>Average base fare/km</strong>
								<span>
									{Number(rideStats.average_base_fare_per_km || 0).toFixed(2)}
								</span>
							</li>
						</ul>
					</div>
				</section>
			) : null}

			<section className="card">
				<h2>All Members In System</h2>
				<ul className="booking-list">
					{members.map(member => (
						<li key={member.member_id}>
							<strong>
								#{member.member_id} {member.full_name} ({member.username})
							</strong>
							<span>{member.email}</span>
							<span>
								Gender: {member.gender} | Reputation: {member.reputation_score}
							</span>
							<span>Phone: {member.phone_number || "-"}</span>
							<span>Created: {new Date(member.created_at).toLocaleString()}</span>
							<span>Role: {member.role}</span>
							<div className="pick-mode">
								<button
									type="button"
									className="btn ghost"
									onClick={() => updateRole(member.member_id, "user")}
								>
									Set User
								</button>
								<button
									type="button"
									className="btn primary"
									onClick={() => updateRole(member.member_id, "admin")}
								>
									Set Admin
								</button>
							</div>
						</li>
					))}
				</ul>
			</section>

			<section className="card">
				<h2>Audit Logs</h2>
				<div className="pick-mode">
					<input
						type="number"
						min="1"
						max="2000"
						value={auditLimit}
						onChange={event => setAuditLimit(Number(event.target.value || 200))}
					/>
					<button
						className="btn primary"
						type="button"
						onClick={() => loadAdminData(auditLimit, unauthorizedLimit)}
					>
						Reload Logs
					</button>
				</div>
				<ul className="booking-list">
					{auditLogs.map((log, index) => (
						<li key={`${log.ts}-${index}`}>
							<strong>
								{log.ts} | {log.action} | {log.status}
							</strong>
							<span>
								Actor: {log.actor_username || "-"} (member{" "}
								{log.actor_member_id ?? "-"})
							</span>
							<span>Details: {JSON.stringify(log.details)}</span>
						</li>
					))}
				</ul>
			</section>

			<section className="card">
				<h2>Unauthorized Direct DB Changes</h2>
				<div className="pick-mode">
					<input
						type="number"
						min="1"
						max="2000"
						value={unauthorizedLimit}
						onChange={event => setUnauthorizedLimit(Number(event.target.value || 200))}
					/>
					<button
						className="btn primary"
						type="button"
						onClick={() => loadAdminData(auditLimit, unauthorizedLimit)}
					>
						Reload Unauthorized
					</button>
				</div>

				{unauthorizedSummary.length > 0 ? (
					<div className="grid-two" style={{ marginTop: 10 }}>
						{unauthorizedSummary.map(row => (
							<div key={`${row.table_name}-${row.operation}`} className="stat-card">
								<h3>
									{row.table_name} | {row.operation}
								</h3>
								<p className="value">{row.total}</p>
							</div>
						))}
					</div>
				) : (
					<p className="subtle" style={{ marginTop: 10 }}>
						No unauthorized DB changes found.
					</p>
				)}

				<ul className="booking-list" style={{ marginTop: 10 }}>
					{unauthorizedChanges.map(change => (
						<li key={change.log_id}>
							<strong>
								#{change.log_id} | {change.created_at} | {change.table_name} |{" "}
								{change.operation}
							</strong>
							<span>
								PK: {change.primary_key_name}={change.primary_key_value}
							</span>
							<span>
								Source: {change.source_tag} | Authorized:{" "}
								{String(change.is_authorized)}
							</span>
							<span>
								DB User: {change.db_user} | Conn: {change.connection_id}
							</span>
							<span>
								App: req={change.app_request_id || "-"}, actor=
								{change.app_actor_username || "-"} (member{" "}
								{change.app_actor_member_id ?? "-"}, role{" "}
								{change.app_actor_role || "-"})
							</span>
							<span>Old: {JSON.stringify(change.old_values_json || {})}</span>
							<span>New: {JSON.stringify(change.new_values_json || {})}</span>
						</li>
					))}
				</ul>
			</section>

			<p className="message">{message}</p>
		</div>
	);
}
