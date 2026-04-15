import React from "react";
import { useState } from "react";

import { api, setToken } from "../api";

const initialRegister = {
	username: "",
	password: "",
	email: "",
	full_name: "",
	phone_number: "",
	gender: "Male",
};

export default function LoginPage() {
	const [mode, setMode] = useState("login");
	const [login, setLogin] = useState({ username: "", password: "" });
	const [register, setRegister] = useState(initialRegister);
	const [message, setMessage] = useState("");

	async function handleLogin(event) {
		event.preventDefault();
		setMessage("Working...");
		try {
			const data = await api.login(login);
			setToken(data.access_token);
			setMessage("Login successful. Go to Rides page.");
		} catch (error) {
			setMessage(error.message);
		}
	}

	async function handleRegister(event) {
		event.preventDefault();
		setMessage("Working...");
		try {
			const payload = { ...register, phone_number: register.phone_number || null };
			const data = await api.register(payload);
			setToken(data.access_token);
			setMessage("Registration successful. Go to Rides page.");
			setRegister(initialRegister);
		} catch (error) {
			setMessage(error.message);
		}
	}

	return (
		<div className="page auth-page">
			<section className="card panel">
				<div className="section-title">
					<div>
						<p className="eyebrow">Account</p>
						<h2>Log in or register to ride.</h2>
						<p className="subtle">Stay signed in to move between booking, hosting, and chat seamlessly.</p>
					</div>
					<div className="auth-toggle">
						<button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
							Login
						</button>
						<button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
							Register
						</button>
					</div>
				</div>

				{mode === "login" ? (
					<form className="form-card" onSubmit={handleLogin}>
						<input
							placeholder="Username"
							value={login.username}
							onChange={e => setLogin({ ...login, username: e.target.value })}
							required
						/>
						<input
							type="password"
							placeholder="Password"
							value={login.password}
							onChange={e => setLogin({ ...login, password: e.target.value })}
							required
						/>
						<button className="btn primary" type="submit">
							Login
						</button>
					</form>
				) : (
					<form className="form-card" onSubmit={handleRegister}>
						<div className="grid-two">
							<input
								placeholder="Username"
								value={register.username}
								onChange={e => setRegister({ ...register, username: e.target.value })}
								minLength={3}
								maxLength={50}
								pattern="^[a-zA-Z0-9_.-]+$"
								title="3-50 characters. Letters, numbers, underscore, dot, and hyphen only."
								required
							/>
							<input
								type="password"
								placeholder="Password"
								value={register.password}
								onChange={e => setRegister({ ...register, password: e.target.value })}
								minLength={6}
								maxLength={64}
								title="Password must be between 6 and 64 characters."
								required
							/>
						</div>
						<div className="grid-two">
							<input
								type="email"
								placeholder="IITGN email"
								value={register.email}
								onChange={e => setRegister({ ...register, email: e.target.value })}
								required
							/>
							<input
								placeholder="Full name"
								value={register.full_name}
								onChange={e => setRegister({ ...register, full_name: e.target.value })}
								required
							/>
						</div>
						<div className="grid-two">
							<input
								placeholder="Phone (optional)"
								value={register.phone_number}
								onChange={e => setRegister({ ...register, phone_number: e.target.value })}
							/>
							<select
								value={register.gender}
								onChange={e => setRegister({ ...register, gender: e.target.value })}
							>
								<option>Male</option>
								<option>Female</option>
								<option>Other</option>
							</select>
						</div>
						<button className="btn primary" type="submit">
							Register
						</button>
					</form>
				)}

				<p className="message">{message}</p>
			</section>
		</div>
	);
}
