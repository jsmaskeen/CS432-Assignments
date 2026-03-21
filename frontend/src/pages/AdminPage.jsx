import React, { useEffect, useState } from "react";

import { api } from "../api";

export default function AdminPage() {
	const [currentUser, setCurrentUser] = useState(null);
	const [members, setMembers] = useState([]);
	const [auditLogs, setAuditLogs] = useState([]);
	const [auditLimit, setAuditLimit] = useState(200);
	const [message, setMessage] = useState("");

	async function loadAdminData(limitValue = auditLimit) {
		setMessage("Loading admin data...");
		try {
			const [meData, membersData, logsData] = await Promise.all([
				api.me(),
				api.listMembersAdmin(),
				api.listAuditLogsAdmin(limitValue),
			]);
			setCurrentUser(meData);
			setMembers(membersData);
			setAuditLogs(logsData);
			setMessage(`Loaded ${membersData.length} members and ${logsData.length} audit records`);
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
			<section className="card">
				<h2>Admin Member Management</h2>
				<ul className="booking-list">
					{members.map(member => (
						<li key={member.member_id}>
							<strong>
								#{member.member_id} {member.full_name} ({member.username})
							</strong>
							<span>{member.email}</span>
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
						onClick={() => loadAdminData(auditLimit)}
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

			<p className="message">{message}</p>
		</div>
	);
}
