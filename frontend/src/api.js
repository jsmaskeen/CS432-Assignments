const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export function getToken() {
	return localStorage.getItem("rajak_token") || "";
}

export function setToken(token) {
	localStorage.setItem("rajak_token", token);
	window.dispatchEvent(new Event("rajak-auth-changed"));
}

export function clearToken() {
	localStorage.removeItem("rajak_token");
	window.dispatchEvent(new Event("rajak-auth-changed"));
}

async function request(path, options = {}) {
	const token = getToken();
	const headers = {
		"Content-Type": "application/json",
		...(options.headers || {}),
	};

	if (token) {
		headers.Authorization = `Bearer ${token}`;
	}

	const response = await fetch(`${API_BASE}${path}`, {
		...options,
		headers,
	});

	const payload = await response.json().catch(() => ({}));
	if (!response.ok) {
		throw new Error(payload.detail || "Request failed");
	}

	return payload;
}

export const api = {
	register: data => request("/auth/register", { method: "POST", body: JSON.stringify(data) }),
	login: data => request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
	me: () => request("/auth/me"),
	promoteToAdmin: username =>
		request("/auth/admin/promote", {
			method: "POST",
			body: JSON.stringify({ username }),
		}),
	listRides: () => request("/rides"),
	createRide: data => request("/rides", { method: "POST", body: JSON.stringify(data) }),
	bookRide: (rideId, data) =>
		request(`/rides/${rideId}/book`, { method: "POST", body: JSON.stringify(data) }),
	myBookings: () => request("/rides/my/bookings"),
	listLocations: ({ search = "", location_type = "", limit = 100 } = {}) => {
		const params = new URLSearchParams();
		if (search) params.set("search", search);
		if (location_type) params.set("location_type", location_type);
		if (limit) params.set("limit", String(limit));
		return request(`/locations?${params.toString()}`);
	},
	myPreference: () => request("/preferences/me"),
	upsertPreference: data =>
		request("/preferences/me", { method: "PUT", body: JSON.stringify(data) }),
	createReview: data => request("/reviews", { method: "POST", body: JSON.stringify(data) }),
	listRideReviews: rideId => request(`/reviews/ride/${rideId}`),
	listMemberReviews: memberId => request(`/reviews/member/${memberId}`),
	updateReview: (reviewId, data) =>
		request(`/reviews/${reviewId}`, { method: "PATCH", body: JSON.stringify(data) }),
	deleteReview: reviewId => request(`/reviews/${reviewId}`, { method: "DELETE" }),
	createSettlement: data =>
		request("/settlements", { method: "POST", body: JSON.stringify(data) }),
	updateSettlementStatus: (settlementId, data) =>
		request(`/settlements/${settlementId}/status`, {
			method: "PATCH",
			body: JSON.stringify(data),
		}),
	mySettlements: () => request("/settlements/my"),
	getBookingSettlement: bookingId => request(`/settlements/booking/${bookingId}`),
	listRideChat: rideId => request(`/chat/ride/${rideId}`),
	sendRideChat: (rideId, data) =>
		request(`/chat/ride/${rideId}`, { method: "POST", body: JSON.stringify(data) }),
	listMembersAdmin: () => request("/admin/members"),
	updateMemberRoleAdmin: (memberId, role) =>
		request(`/admin/members/${memberId}/role`, {
			method: "PATCH",
			body: JSON.stringify({ role }),
		}),
	getRideStatsAdmin: () => request("/admin/rides/stats"),
	listAuditLogsAdmin: (limit = 200) => request(`/admin/audit-logs?limit=${limit}`),
	listUnauthorizedDbChangesAdmin: (limit = 200) =>
		request(`/admin/db-audit/unauthorized?limit=${limit}`),
	listUnauthorizedDbSummaryAdmin: () => request("/admin/db-audit/unauthorized/summary"),
};
