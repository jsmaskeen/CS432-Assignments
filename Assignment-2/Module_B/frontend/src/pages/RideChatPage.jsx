import React, { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, getToken } from "../api";

export default function RideChatPage() {
	const { rideId } = useParams();
	const [ride, setRide] = useState(null);
	const [messages, setMessages] = useState([]);
	const [messageBody, setMessageBody] = useState("");
	const [status, setStatus] = useState("Connecting...");
	const [currentUser, setCurrentUser] = useState(null);
	const wsRef = useRef(null);
	const scrollRef = useRef(null);

	useEffect(() => {
		let active = true;
		async function loadRide() {
			if (!rideId) {
				return;
			}
			try {
				const data = await api.getRide(rideId);
				if (active) {
					setRide(data);
				}
			} catch (error) {
				if (active) {
					setStatus(error.message || "Failed to load ride details");
				}
			}
		}

		loadRide();
		return () => {
			active = false;
		};
	}, [rideId]);

	useEffect(() => {
		let active = true;
		async function loadMe() {
			try {
				const data = await api.me();
				if (active) {
					setCurrentUser(data);
				}
			} catch {
				if (active) {
					setCurrentUser(null);
				}
			}
		}

		loadMe();
		return () => {
			active = false;
		};
	}, []);

	useEffect(() => {
		let cancelled = false;
		async function loadHistory() {
			if (!rideId) {
				return;
			}
			try {
				const data = await api.listRideChat(rideId);
				if (!cancelled) {
					setMessages(data || []);
				}
			} catch (error) {
				if (!cancelled) {
					setStatus(error.message || "Failed to load chat history");
				}
			}
		}

		loadHistory();
		return () => {
			cancelled = true;
		};
	}, [rideId]);

	useEffect(() => {
		const token = getToken();
		if (!rideId || !token) {
			setStatus("Login required for chat");
			return () => {};
		}

		const wsUrl = api.chatWebSocketUrl(rideId, token);
		const socket = new WebSocket(wsUrl);
		wsRef.current = socket;
		setStatus("Connecting...");

		socket.onopen = () => {
			setStatus("Connected");
		};
		socket.onmessage = event => {
			try {
				const payload = JSON.parse(event.data);
				if (payload?.MessageID || payload?.message_body) {
					setMessages(prev => [
						...prev,
						{
							MessageID: payload.MessageID || `local-${Date.now()}`,
							RideID: Number(rideId),
							Sender_MemberID: payload.Sender_MemberID,
							Sender_Name: payload.Sender_Name,
							Message_Body: payload.Message_Body || payload.message_body,
							Sent_At: payload.Sent_At || new Date().toISOString(),
						},
					]);
				}
			} catch {
				// Ignore malformed messages.
			}
		};
		socket.onerror = () => {
			setStatus("Chat connection error");
		};
		socket.onclose = () => {
			setStatus("Disconnected");
		};

		return () => {
			socket.close();
		};
	}, [rideId]);

	useEffect(() => {
		if (scrollRef.current) {
			scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
		}
	}, [messages]);

	function handleSend(event) {
		event.preventDefault();
		const text = messageBody.trim();
		if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
			return;
		}
		wsRef.current.send(JSON.stringify({ message_body: text }));
		setMessageBody("");
	}

	return (
		<div className="page">
			<section className="card panel">
				<div className="section-title">
					<div>
						<h2>Ride Chat {ride ? `#${ride.RideID}` : ""}</h2>
						<p className="message">{status}</p>
					</div>
					<Link to="/bookings" className="btn ghost">
						Back to bookings
					</Link>
				</div>
				<div
					className="chat-window"
					ref={scrollRef}
					style={{
						maxHeight: 420,
						overflowY: "auto",
						display: "grid",
						gap: 12,
						padding: 12,
						background: "rgba(255, 255, 255, 0.04)",
						borderRadius: 12,
					}}
				>
					{messages.length === 0 ? (
						<p className="message">No messages yet.</p>
					) : null}
					{messages.map(message => (
						<div
							key={message.MessageID}
							className="chat-bubble"
							style={{
								maxWidth: "70%",
								justifySelf:
									currentUser && message.Sender_MemberID === currentUser.member_id
										? "end"
										: "start",
								background:
									currentUser && message.Sender_MemberID === currentUser.member_id
										? "rgba(123, 77, 255, 0.25)"
										: "rgba(255, 255, 255, 0.08)",
								padding: "10px 14px",
								borderRadius: 12,
							}}
						>
							<div className="small">
								{message.Sender_Name || `Member #${message.Sender_MemberID || ""}`}
							</div>
							<p style={{ margin: "6px 0" }}>{message.Message_Body}</p>
							<div className="small">
								{message.Sent_At
									? new Date(message.Sent_At).toLocaleString()
									: ""}
							</div>
						</div>
					))}
				</div>
				<form className="form-card compact" onSubmit={handleSend}>
					<input
						placeholder="Type a message"
						value={messageBody}
						onChange={event => setMessageBody(event.target.value)}
						style={{ padding: "12px 14px" }}
						maxLength={2000}
						required
					/>
					<button className="btn primary" type="submit">
						Send
					</button>
				</form>
			</section>
		</div>
	);
}
