import React from "react";
import { Link } from "react-router-dom";

const features = [
	{
		title: "Tap, match, ride",
		text: "Pick start/end, see live supply, and lock a seat in under a minute.",
	},
	{
		title: "Host with control",
		text: "Publish rides with capacity, fare, and timing controls so you stay in charge.",
	},
	{
		title: "Campus-trusted",
		text: "IITGN identity, ride chat, and preferences keep coordination clean and safe.",
	},
];

const steps = [
	"Set pickup & drop with one tap on the map",
	"Pick the ride that matches price, seats, and timing",
	"Chat, arrive, and settle without friction",
];

export default function HomePage() {
	return (
		<div className="page home-page">
			<section className="hero">
				<div className="hero-copy">
					<p className="eyebrow">Campus Uber, but calmer</p>
					<h1>Book and share rides that feel like Uber, built for IITGN.</h1>
					<p>
						All the good parts of the Uber flow—map-first discovery, one-tap booking,
						and transparent fares—tailored for your campus community.
					</p>
					<div className="hero-actions">
						<Link to="/rides" className="btn primary">
							Book a ride
						</Link>
						<Link to="/rides" className="btn ghost">
							Host a ride
						</Link>
						<span className="pill success">Avg match under 5 min</span>
					</div>
					<div className="list-inline" style={{ marginTop: 10 }}>
						{steps.map(step => (
							<span key={step} className="pill">
								{step}
							</span>
						))}
					</div>
				</div>
				<div className="hero-blob">
					<div className="map-overlay" style={{ position: "absolute", top: 18, left: 18 }}>
						<div className="overlay-card">
							<div className="section-title">
								<strong>Live campus rides</strong>
								<span className="pill">15 active</span>
							</div>
							<div className="chip-row">
								<span className="pill success">Most to Ahmedabad</span>
								<span className="pill">Sedan • Hatch • SUV</span>
							</div>
						</div>
					</div>
				</div>
			</section>

			<section className="stats-grid">
				<div className="stat-card">
					<h3>Built for students</h3>
					<div className="value">IITGN only</div>
					<p className="subtle">Identity, chat, and preferences scoped to campus.</p>
				</div>
				<div className="stat-card">
					<h3>Ride coverage</h3>
					<div className="value">24/7</div>
					<p className="subtle">Airport, city, and campus loops in one view.</p>
				</div>
				<div className="stat-card">
					<h3>Fares you can see</h3>
					<div className="value">₹ transparent</div>
					<p className="subtle">Hosts set base fare per km with clear seats left.</p>
				</div>
			</section>

			<section className="features">
				{features.map(item => (
					<article key={item.title} className="feature-card">
						<h3>{item.title}</h3>
						<p className="subtle">{item.text}</p>
					</article>
				))}
			</section>
		</div>
	);
}
