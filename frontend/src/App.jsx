import React from "react";
import { Link, Route, Routes } from "react-router-dom";

import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import RidesPage from "./pages/RidesPage";

export default function App() {
	return (
		<div className="app-shell">
			<header className="top-nav">
				<div className="brand">RAJAK</div>
				<nav>
					<Link to="/">Home</Link>
					<Link to="/auth">Login/Register</Link>
					<Link to="/rides">Rides</Link>
				</nav>
			</header>

			<main>
				<Routes>
					<Route path="/" element={<HomePage />} />
					<Route path="/auth" element={<LoginPage />} />
					<Route path="/rides" element={<RidesPage />} />
				</Routes>
			</main>
		</div>
	);
}
