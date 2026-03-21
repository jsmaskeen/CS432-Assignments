import React from "react";
import { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes } from "react-router-dom";

import { api, clearToken, getToken } from "./api";
import AdminPage from "./pages/AdminPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import LocationsPage from "./pages/LocationsPage";
import MyBookingsPage from "./pages/MyBookingsPage";
import PreferencesPage from "./pages/PreferencesPage";
import ProfilePage from "./pages/ProfilePage";
import ReviewsPage from "./pages/ReviewsPage";
import RidesPage from "./pages/RidesPageNew";
import SavedLocationsPage from "./pages/SavedLocationsPage";
import SettlementsPage from "./pages/SettlementsPage";

export default function App() {
	const [currentUser, setCurrentUser] = useState(undefined);

	useEffect(() => {
		async function loadMe() {
			if (!getToken()) {
				setCurrentUser(null);
				return;
			}
			try {
				const data = await api.me();
				setCurrentUser(data);
			} catch {
				setCurrentUser(null);
			}
		}

		loadMe();
		window.addEventListener("rajak-auth-changed", loadMe);
		window.addEventListener("storage", loadMe);
		return () => {
			window.removeEventListener("rajak-auth-changed", loadMe);
			window.removeEventListener("storage", loadMe);
		};
	}, []);

	return (
		<div className="app-shell">
			<header className="top-nav">
				<div className="brand">
					<span>RAJAK</span>
					<span className="brand-pill">Campus</span>
				</div>
				<nav className="nav-links">
					<NavLink className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} to="/">
						Home
					</NavLink>
					{currentUser ? (
						<>
							<NavLink className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} to="/rides">
								Create a booking
							</NavLink>
							<NavLink className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} to="/bookings">
								My Bookings
							</NavLink>
							<NavLink className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} to="/saved-locations">
								Saved Locations
							</NavLink>
							<NavLink className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} to="/profile">
								Profile
							</NavLink>
							{currentUser?.role === "admin" ? (
								<NavLink className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} to="/admin">
									Admin
								</NavLink>
							) : null}
						</>
					) : null}
				</nav>
				<div className="nav-actions">
					{currentUser ? (
						<>
							<Link to="/rides" className="btn primary">
								Book a ride
							</Link>
							<div className="user-chip">
								<div className="avatar">{currentUser.full_name?.[0] || "U"}</div>
								<div>
									<div style={{ fontWeight: 600 }}>{currentUser.full_name || currentUser.username}</div>
									<div className="small">{currentUser.role}</div>
								</div>
								<button className="btn text" type="button" onClick={clearToken}>
									Logout
								</button>
							</div>
						</>
					) : (
						<Link to="/auth" className="btn primary">
							Login / Register
						</Link>
					)}
				</div>
			</header>

			<main>
				<Routes>
					<Route path="/" element={<HomePage />} />
					<Route path="/auth" element={<LoginPage />} />
					<Route
						path="/bookings"
						element={
							<RequireAuth user={currentUser}>
								<MyBookingsPage />
							</RequireAuth>
						}
					/>
					<Route
						path="/rides"
						element={
							<RequireAuth user={currentUser}>
								<RidesPage />
							</RequireAuth>
						}
					/>
					<Route
						path="/locations"
						element={
							<RequireAuth user={currentUser}>
								<LocationsPage />
							</RequireAuth>
						}
					/>
					<Route
						path="/saved-locations"
						element={
							<RequireAuth user={currentUser}>
								<SavedLocationsPage />
							</RequireAuth>
						}
					/>
					<Route
						path="/profile"
						element={
							<RequireAuth user={currentUser}>
								<ProfilePage />
							</RequireAuth>
						}
					/>
					<Route
						path="/preferences"
						element={
							<RequireAuth user={currentUser}>
								<PreferencesPage />
							</RequireAuth>
						}
					/>
					<Route
						path="/reviews"
						element={
							<RequireAuth user={currentUser}>
								<ReviewsPage />
							</RequireAuth>
						}
					/>
					<Route
						path="/settlements"
						element={
							<RequireAuth user={currentUser}>
								<SettlementsPage />
							</RequireAuth>
						}
					/>
					<Route
						path="/admin"
						element={
							<RequireAuth user={currentUser}>
								<AdminPage />
							</RequireAuth>
						}
					/>
					<Route path="*" element={<Navigate to="/" replace />} />
				</Routes>
			</main>
		</div>
	);
}

function RequireAuth({ user, children }) {
	if (user === undefined) {
		return (
			<div className="page">
				<p className="message">Checking session...</p>
			</div>
		);
	}

	if (!user) {
		return <Navigate to="/auth" replace />;
	}

	return children;
}
