import React from "react";
import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { api, clearToken, getToken } from "./api";
import AdminPage from "./pages/AdminPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import LocationsPage from "./pages/LocationsPage";
import PreferencesPage from "./pages/PreferencesPage";
import ReviewsPage from "./pages/ReviewsPage";
import RidesPage from "./pages/RidesPage";
import SettlementsPage from "./pages/SettlementsPage";

export default function App() {
	const [currentUser, setCurrentUser] = useState(null);

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
				<div className="brand">RAJAK</div>
				<nav>
					<Link to="/">Home</Link>
					{currentUser ? (
						<Link to="/auth">Logged in ({currentUser.full_name})</Link>
					) : (
						<Link to="/auth">Login/Register</Link>
					)}
					<Link to="/rides">Rides</Link>
					<Link to="/locations">Locations</Link>
					<Link to="/preferences">Preferences</Link>
					<Link to="/reviews">Reviews</Link>
					<Link to="/settlements">Settlements</Link>
					{currentUser?.role === "admin" ? <Link to="/admin">Admin</Link> : null}
					{currentUser ? (
						<button className="btn ghost" type="button" onClick={clearToken}>
							Logout
						</button>
					) : null}
				</nav>
			</header>

			<main>
				<Routes>
					<Route path="/" element={<HomePage />} />
					<Route path="/auth" element={<LoginPage />} />
					<Route path="/rides" element={<RidesPage />} />
					<Route path="/locations" element={<LocationsPage />} />
					<Route path="/preferences" element={<PreferencesPage />} />
					<Route path="/reviews" element={<ReviewsPage />} />
					<Route path="/settlements" element={<SettlementsPage />} />
					<Route path="/admin" element={<AdminPage />} />
				</Routes>
			</main>
		</div>
	);
}
