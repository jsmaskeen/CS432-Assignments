import React, { useEffect, useState } from "react";

import { api } from "../api";

const defaultCreate = {
	ride_id: "",
	reviewee_member_id: "",
	rating: 5,
	comments: "",
};

export default function ReviewsPage() {
	const [currentUser, setCurrentUser] = useState(null);
	const [createForm, setCreateForm] = useState(defaultCreate);
	const [memberIdQuery, setMemberIdQuery] = useState("");
	const [memberReviews, setMemberReviews] = useState([]);
	const [message, setMessage] = useState("");

	useEffect(() => {
		api.me()
			.then(data => {
				setCurrentUser(data);
				setMemberIdQuery(String(data.member_id));
			})
			.catch(error => setMessage(error.message));
	}, []);

	useEffect(() => {
		if (!currentUser?.member_id) {
			return;
		}
		api.listMemberReviews(currentUser.member_id)
			.then(data => setMemberReviews(data || []))
			.catch(error => setMessage(error.message));
	}, [currentUser]);

	return (
		<div className="page">
			<section className="card">
				<h2>My Reviews</h2>
				{currentUser ? (
					<div className="chip-row" style={{ marginBottom: 12 }}>
						<span className="pill success">
							Current rating {currentUser.reputation_score ?? "-"}
						</span>
						<span className="pill">Member #{currentUser.member_id}</span>
					</div>
				) : (
					<p className="message">Loading your rating...</p>
				)}
				<div className="rides-list">
					<section className="card panel">
						<h3>Reviews about me</h3>
						<ul className="booking-list">
							{memberReviews
								.filter(review => review.Reviewee_MemberID === currentUser?.member_id)
								.map(review => (
									<li key={`about-${review.ReviewID}`}>
										<strong>
											Ride #{review.RideID} | {review.Rating}/5
										</strong>
										<span>
											Reviewer {review.Reviewer_Name || `#${review.Reviewer_MemberID}`}
										</span>
										<span>{review.Comments || "No comments"}</span>
									</li>
								))}
							{memberReviews.filter(
								review => review.Reviewee_MemberID === currentUser?.member_id,
							).length === 0 ? (
								<li>No reviews about you yet.</li>
							) : null}
						</ul>
					</section>
					<section className="card panel">
						<h3>Reviews I've given</h3>
						<ul className="booking-list">
							{memberReviews
								.filter(review => review.Reviewer_MemberID === currentUser?.member_id)
								.map(review => (
									<li key={`given-${review.ReviewID}`}>
										<strong>
											Ride #{review.RideID} | {review.Rating}/5
										</strong>
										<span>
											Reviewee {review.Reviewee_Name || `#${review.Reviewee_MemberID}`}
										</span>
										<span>{review.Comments || "No comments"}</span>
									</li>
								))}
							{memberReviews.filter(
								review => review.Reviewer_MemberID === currentUser?.member_id,
							).length === 0 ? (
								<li>No reviews given yet.</li>
							) : null}
						</ul>
					</section>
				</div>
			</section>

			<p className="message">{message}</p>
		</div>
	);
}
