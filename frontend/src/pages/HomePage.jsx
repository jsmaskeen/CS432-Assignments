import React from "react";
import { Link } from "react-router-dom";

const features = [
	{
		title: "Campus-first rides",
		text: "Discover rides around IITGN with quick filters and soft onboarding.",
	},
	{
		title: "Low-friction booking",
		text: "Book seats in seconds with transparent route and fare inputs.",
	},
	{
		title: "Student identity",
		text: "Designed around IITGN email-based community trust and safety.",
	},
];

export default function HomePage() {
	return (
		<div className="page home-page">
			<section className="hero">
				<div className="hero-copy">
					<p className="eyebrow">Ride Along - Just Act Kool</p>
					<h1>Cab sharing for IITGN, made calm and colorful.</h1>
					<p>
						RAJAK helps students host rides, find seats, and coordinate daily travel
						with less noise and more clarity.
					</p>
					<div className="hero-actions">
						<Link to="/auth" className="btn primary">
							Get Started
						</Link>
						<Link to="/rides" className="btn ghost">
							Browse Rides
						</Link>
					</div>
				</div>
				<div className="hero-blob" />
			</section>

			<section className="features">
				{features.map(item => (
					<article key={item.title} className="feature-card">
						<h3>{item.title}</h3>
						<p>{item.text}</p>
					</article>
				))}
			</section>
		</div>
	);
}
