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
	const [rideIdQuery, setRideIdQuery] = useState("");
	const [memberIdQuery, setMemberIdQuery] = useState("");
	const [reviews, setReviews] = useState([]);
	const [message, setMessage] = useState("");

	useEffect(() => {
		api.me()
			.then(data => {
				setCurrentUser(data);
				setMemberIdQuery(String(data.member_id));
			})
			.catch(error => setMessage(error.message));
	}, []);

	async function loadByRide() {
		if (!rideIdQuery) {
			setMessage("Enter ride id");
			return;
		}
		try {
			const data = await api.listRideReviews(Number(rideIdQuery));
			setReviews(data);
			setMessage(`Loaded ${data.length} reviews for ride ${rideIdQuery}`);
		} catch (error) {
			setMessage(error.message);
		}
	}

	async function loadByMember() {
		if (!memberIdQuery) {
			setMessage("Enter member id");
			return;
		}
		try {
			const data = await api.listMemberReviews(Number(memberIdQuery));
			setReviews(data);
			setMessage(`Loaded ${data.length} reviews for member ${memberIdQuery}`);
		} catch (error) {
			setMessage(error.message);
		}
	}

	async function handleCreate(event) {
		event.preventDefault();
		setMessage("Creating review...");
		try {
			await api.createReview({
				ride_id: Number(createForm.ride_id),
				reviewee_member_id: Number(createForm.reviewee_member_id),
				rating: Number(createForm.rating),
				comments: createForm.comments || null,
			});
			setCreateForm(defaultCreate);
			setMessage("Review created");
		} catch (error) {
			setMessage(error.message);
		}
	}

	return (
		<div className="page">
			<section className="card">
				<h2>Reviews</h2>
				{currentUser ? <p>Current member id: {currentUser.member_id}</p> : null}
				<form className="form-card compact" onSubmit={handleCreate}>
					<input
						type="number"
						placeholder="Ride ID"
						value={createForm.ride_id}
						onChange={event =>
							setCreateForm({ ...createForm, ride_id: event.target.value })
						}
						required
					/>
					<input
						type="number"
						placeholder="Reviewee Member ID"
						value={createForm.reviewee_member_id}
						onChange={event =>
							setCreateForm({ ...createForm, reviewee_member_id: event.target.value })
						}
						required
					/>
					<input
						type="number"
						min="1"
						max="5"
						placeholder="Rating"
						value={createForm.rating}
						onChange={event =>
							setCreateForm({ ...createForm, rating: event.target.value })
						}
						required
					/>
					<input
						placeholder="Comments"
						value={createForm.comments}
						onChange={event =>
							setCreateForm({ ...createForm, comments: event.target.value })
						}
					/>
					<button className="btn primary" type="submit">
						Create Review
					</button>
				</form>
			</section>

			<section className="card">
				<h3>Find reviews</h3>
				<div className="form-card compact">
					<input
						type="number"
						placeholder="Ride ID"
						value={rideIdQuery}
						onChange={event => setRideIdQuery(event.target.value)}
					/>
					<button className="btn ghost" onClick={loadByRide} type="button">
						Load by ride
					</button>
					<input
						type="number"
						placeholder="Member ID"
						value={memberIdQuery}
						onChange={event => setMemberIdQuery(event.target.value)}
					/>
					<button className="btn ghost" onClick={loadByMember} type="button">
						Load by member
					</button>
				</div>
				<ul className="booking-list">
					{reviews.map(review => (
						<li key={review.ReviewID}>
							<strong>
								Ride #{review.RideID} | {review.Rating}/5
							</strong>
							<span>
								Reviewer {review.Reviewer_MemberID}
								{" -> "}
								Reviewee {review.Reviewee_MemberID}
							</span>
							<span>{review.Comments || "No comments"}</span>
						</li>
					))}
				</ul>
			</section>

			<p className="message">{message}</p>
		</div>
	);
}
