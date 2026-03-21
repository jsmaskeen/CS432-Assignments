import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from "react-leaflet";
import { api } from "../api";

export default function RidesPage() {
	const [mappedRides, setMappedRides] = useState([]);
	const [selectedRideId, setSelectedRideId] = useState(null);
	const [selectedRide, setSelectedRide] = useState(null);
	const [myBookings, setMyBookings] = useState([]);

	const [rideForm, setRideForm] = useState({
		start_geohash: "",
							<h3>Available rides</h3>
							<span className="pill">{mappedRides.length} live</span>
						</div>

						<div className="rides-list">
							{mappedRides.map(ride => (
								<button
									key={ride.RideID}
									className={`ride-card ${selectedRideId === ride.RideID ? "selected" : ""}`}
									onClick={() => setSelectedRideId(ride.RideID)}
								>
									<div className="section-title">
										<strong>Ride #{ride.RideID}</strong>
										<span className="pill">{ride.Vehicle_Type || "—"}</span>
									</div>
									{hasCoords ? (
										<Polyline
											positions={[ride.start, ride.end]}
											pathOptions={{ color: ride.RideID === selectedRideId ? "#0beb87" : "#65a4ff", weight: ride.RideID === selectedRideId ? 4 : 2 }}
										/>
									) : null}

									{hasCoords ? (
										<Marker position={ride.start}>
											<Popup>Start • Ride #{ride.RideID}</Popup>
										</Marker>
									) : null}

									{hasCoords ? (
										<Marker position={ride.end}>
											<Popup>End • Ride #{ride.RideID}</Popup>
										</Marker>
									) : null}
								</React.Fragment>
							);
						})}

						{selectedRide && Array.isArray(selectedRide.start) && Array.isArray(selectedRide.end) ? (
							<>
								<Marker position={selectedRide.start}>
									<Popup>Selected start</Popup>
								</Marker>
								<Marker position={selectedRide.end}>
									<Popup>Selected end</Popup>
								</Marker>
							</>
						) : null}
					</MapContainer>
				</div>
			</div>

			<section style={{ padding: "1rem" }}>
				<form className="form-card compact" onSubmit={handleBookRide}>
					<div className="section-title">
						import React, { useEffect, useState } from 'react';
						import { Link } from 'react-router-dom';
						import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
						import { api } from '../api';

						export default function RidesPage() {
						  const [rides, setRides] = useState([]);
						  const [selectedId, setSelectedId] = useState(null);
						  const [message, setMessage] = useState('');

						  useEffect(() => {
						    api
						      .listRides()
						      .then(r => setRides(r || []))
						      .catch(() => setMessage('Failed to load rides'));
						  }, []);

						  const selected = rides.find(r => r.RideID === selectedId) || null;

						  function Focus({ ride }) {
						    const map = useMap();
						    useEffect(() => {
						      if (!ride || !Array.isArray(ride.start)) return;
						      try {
						        map.flyTo(ride.start, 12, { duration: 0.6 });
						      } catch (e) {
						        // ignore
						      }
						    }, [map, ride]);
						    return null;
						  }

						  return (
						    <div className="page rides-page">
						      <div className="panel panel-strong">
						        <div className="section-title">
						          <div>
						            <p className="eyebrow">Book & host</p>
						            <h2>Live rides</h2>
						          </div>
						          <div className="chip-row">
						            <Link to="/" className="btn ghost">
						              Home
						            </Link>
						            <Link to="/auth" className="btn primary">
						              Login / Switch
						            </Link>
						          </div>
						        </div>
						      </div>

						      <div className="rides-layout">
						        <div className="stack">
						          <section className="card panel">
						            <div className="section-title">
						              <h3>Available rides</h3>
						              <span className="pill">{rides.length}</span>
						            </div>
						            <div className="rides-list">
						              {rides.map(r => (
						                <button key={r.RideID} className={`ride-card ${selectedId === r.RideID ? 'selected' : ''}`} onClick={() => setSelectedId(r.RideID)}>
						                  <div className="section-title">
						                    <strong>Ride #{r.RideID}</strong>
						                    <span className="pill">{r.Vehicle_Type || '—'}</span>
						                  </div>
						                  <div className="chip-row">
						                    <span className="pill success">Seats {r.Available_Seats}/{r.Max_Capacity}</span>
						                    <span className="pill">₹{r.Base_Fare_Per_KM} per km</span>
						                  </div>
						                  <div className="list-inline">
						                    <span>{r.Start_GeoHash || '—'}</span>
						                    <span>→</span>
						                    <span>{r.End_GeoHash || '—'}</span>
						                  </div>
						                </button>
						              ))}
						            </div>
						          </section>
						        </div>

						        <div className="map-shell card panel map-stage">
						          <div className="map-head">
						            <h2>Map</h2>
						            <p>Click a ride to focus the map.</p>
						          </div>

						          <MapContainer center={(selected && Array.isArray(selected.start) ? selected.start : [12.97, 77.59])} zoom={12} style={{ height: 520 }}>
						            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
						            <Focus ride={selected} />
						            {rides.map(r => {
						              const hasCoords = Array.isArray(r.start) && Array.isArray(r.end);
						              return (
						                <React.Fragment key={`m-${r.RideID}`}>
						                  {hasCoords ? <Polyline positions={[r.start, r.end]} pathOptions={{ color: selectedId === r.RideID ? '#0beb87' : '#65a4ff', weight: selectedId === r.RideID ? 4 : 2 }} /> : null}
						                  {hasCoords ? <Marker position={r.start}><Popup>Start (Ride #{r.RideID})</Popup></Marker> : null}
						                  {hasCoords ? <Marker position={r.end}><Popup>End (Ride #{r.RideID})</Popup></Marker> : null}
						                </React.Fragment>
						              );
						            })}
						          </MapContainer>
						        </div>
						      </div>

						      <p className="message">{message}</p>
						    </div>
						  );
						}

											<section className="card panel">
												<div className="section-title">
													<h3>My bookings</h3>
													<span className="pill">{myBookings.length}</span>
												</div>
												<ul className="booking-list">
													{myBookings.map(b => (
														<li key={b.BookingID}>
															<strong>Booking #{b.BookingID}</strong>
															<span>
																Ride #{b.RideID} | {b.Booking_Status}
															</span>
															<span>
																{b.Pickup_GeoHash} → {b.Drop_GeoHash}
															</span>
														</li>
													))}
												</ul>
											</section>

											<section className="card panel">
												<div className="section-title">
													<h3>Create a ride</h3>
													<span className="pill">Host</span>
												</div>
												<form className="form-card compact" onSubmit={handleCreateRide}>
													<input
														placeholder="Start geohash or lat,lng"
														value={rideForm.start_geohash}
														onChange={e => setRideForm({ ...rideForm, start_geohash: e.target.value })}
														required
													/>
													<input
														placeholder="End geohash or lat,lng"
														value={rideForm.end_geohash}
														onChange={e => setRideForm({ ...rideForm, end_geohash: e.target.value })}
														required
													/>
													<input
														type="datetime-local"
														value={rideForm.departure_time}
														onChange={e => setRideForm({ ...rideForm, departure_time: e.target.value })}
														required
													/>
													<div className="two-column-small">
														<input
															placeholder="Vehicle type"
															value={rideForm.vehicle_type}
															onChange={e => setRideForm({ ...rideForm, vehicle_type: e.target.value })}
														/>
														<input
															type="number"
															min="1"
															max="10"
															placeholder="Max capacity"
															value={rideForm.max_capacity}
															onChange={e => setRideForm({ ...rideForm, max_capacity: e.target.value })}
														/>
													</div>
													<input
														type="number"
														min="1"
														step="0.01"
														placeholder="Fare per km"
														value={rideForm.base_fare_per_km}
														onChange={e => setRideForm({ ...rideForm, base_fare_per_km: e.target.value })}
													/>
													<button className="btn primary" type="submit">
														Publish ride
													</button>
												</form>
											</section>

											<section className="card panel">
												<div className="section-title">
													<h3>Ride chat {selectedRideId ? `(Ride #${selectedRideId})` : ""}</h3>
												</div>
												<form className="form-card compact" onSubmit={handleSendChat}>
													<input placeholder="Type a message" value={chatDraft} onChange={e => setChatDraft(e.target.value)} />
													<button className="btn primary" type="submit">
														Send message
													</button>
												</form>
												<ul className="booking-list">
													{chatMessages.map(m => (
														<li key={m.MessageID}>
															<strong>Member #{m.Sender_MemberID}</strong>
															<span>{m.Message_Body}</span>
															<span className="small muted">{m.Sent_At ? new Date(m.Sent_At).toLocaleString() : ""}</span>
														</li>
													))}
												</ul>
											</section>
										</div>

										<div className="map-shell card panel map-stage">
											<div className="map-head">
												<h2>Live rides map</h2>
												<p>Rides are shown as lines between start and end when coordinates are available.</p>
											</div>

											<MapContainer center={mapCenter} zoom={12} className="rides-map" style={{ height: 520 }}>
												<TileLayer
													attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
													url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
												/>

												<FocusMapToRide ride={selectedRide} />

												{mappedRides.map(ride => {
													const hasCoords = Array.isArray(ride.start) && Array.isArray(ride.end);
													return (
														<React.Fragment key={`map-${ride.RideID}`}>
															{hasCoords ? (
																<Polyline
																	positions={[ride.start, ride.end]}
																	pathOptions={{ color: ride.RideID === selectedRideId ? "#0beb87" : "#65a4ff", weight: ride.RideID === selectedRideId ? 4 : 2 }}
																/>
															) : null}

															{hasCoords ? (
																<Marker position={ride.start}>
																	<Popup>Start • Ride #{ride.RideID}</Popup>
																</Marker>
															) : null}

															{hasCoords ? (
																<Marker position={ride.end}>
																	<Popup>End • Ride #{ride.RideID}</Popup>
																</Marker>
															) : null}
														</React.Fragment>
													);
												})}

												{selectedRide && Array.isArray(selectedRide.start) && Array.isArray(selectedRide.end) ? (
													<>
														<Marker position={selectedRide.start}>
															<Popup>Selected start</Popup>
														</Marker>
														<Marker position={selectedRide.end}>
															<Popup>Selected end</Popup>
														</Marker>
													</>
												) : null}
											</MapContainer>
										</div>
									</div>

									<section style={{ padding: "1rem" }}>
										<form className="form-card compact" onSubmit={handleBookRide}>
											<div className="section-title">
												<h3>Confirm booking</h3>
												<span className="pill">{selectedRideId ? `Ride #${selectedRideId}` : "No ride selected"}</span>
											</div>

											<div className="two-column-small">
												<input
													placeholder="Pickup geohash or lat,lng"
													value={bookingForm.pickup_geohash}
													onChange={e => setBookingForm({ ...bookingForm, pickup_geohash: e.target.value })}
													required
												/>
												<input
													placeholder="Drop geohash or lat,lng"
													value={bookingForm.drop_geohash}
													onChange={e => setBookingForm({ ...bookingForm, drop_geohash: e.target.value })}
													required
												/>
											</div>

											<input
												type="number"
												min="0.1"
												step="0.1"
												placeholder="Distance (km)"
												value={bookingForm.distance_travelled_km}
												onChange={e => setBookingForm({ ...bookingForm, distance_travelled_km: e.target.value })}
												required
											/>

											<button className="btn primary" type="submit">
												Confirm booking
											</button>
										</form>

										<p className="message">{message}</p>
									</section>
								</div>
							);
						}
								<input
									placeholder="Type a message"
									value={chatDraft}
									onChange={event => setChatDraft(event.target.value)}
								/>
								<button className="btn primary" type="submit">
									Send message
								</button>
							</form>
							<ul className="booking-list">
								{chatMessages.map(messageItem => (
									<li key={messageItem.MessageID}>
										<strong>Member #{messageItem.Sender_MemberID}</strong>
										<span>{messageItem.Message_Body}</span>
										<span>{new Date(messageItem.Sent_At).toLocaleString()}</span>
									</li>
								))}
							</ul>
						</section>

						{currentUser?.role === "admin" ? (
							<section className="card panel">
								<div className="section-title">
									<h3>Admin actions</h3>
									<span className="pill warn">Promote user</span>
								</div>
								<form className="form-card compact" onSubmit={handlePromote}>
									<input
										placeholder="Username to promote"
										value={promoteUsername}
										onChange={e => setPromoteUsername(e.target.value)}
										required
									/>
									<button className="btn primary" type="submit">
										Promote to admin
									</button>
								</form>
							</section>
						) : null}
					</div>

					<div className="map-shell card panel map-stage">
						<div className="map-head">
							<h2>Live rides map</h2>
							<p>Click to drop pins for booking or hosting. Selecting a ride highlights its path.</p>
						</div>
						<MapContainer center={mapCenter} zoom={11} className="rides-map">
							<TileLayer
								attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
								url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
							/>
							<FocusSelectedRide selectedRide={selectedRide} />
							<MapClickCapture onPick={handleMapPick} />

							{mappedRides.map(ride => (
								<React.Fragment key={`map-${ride.RideID}`}>
									<Polyline
										positions={[ride.start, ride.end]}
										pathOptions={{
											color: ride.RideID === selectedRideId ? "#0beb87" : "#65a4ff",
											dashArray: "10 10",
											weight: ride.RideID === selectedRideId ? 4 : 2,
										}}
									/>
								</React.Fragment>
							))}

							{selectedRide ? (
								<>
									<Marker position={selectedRide.start} icon={selectedStartIcon}>
										<Popup>Ride #{selectedRide.RideID} start</Popup>
									</Marker>
									<Marker position={selectedRide.end} icon={endIcon}>
										<Popup>Ride #{selectedRide.RideID} destination</Popup>
									</Marker>
								</>
							) : null}

							{draftStart ? (
								<Marker position={draftStart} icon={selectedStartIcon}>
									<Popup>Create ride start ({rideForm.start_geohash})</Popup>
								</Marker>
							) : null}
							{draftEnd ? (
								<Marker position={draftEnd} icon={endIcon}>
									<Popup>Create ride end ({rideForm.end_geohash})</Popup>
								</Marker>
							) : null}
							{draftStart && draftEnd ? (
								<Polyline positions={[draftStart, draftEnd]} pathOptions={{ color: "#34a853", weight: 3 }} />
							) : null}
							{draftPickup ? (
								<Marker position={draftPickup} icon={startIcon}>
									<Popup>Booking pickup ({bookingForm.pickup_geohash})</Popup>
								</Marker>
							) : null}
							{draftDrop ? (
								<Marker position={draftDrop} icon={endIcon}>
									<Popup>Booking drop ({bookingForm.drop_geohash})</Popup>
								</Marker>
							) : null}
							{draftPickup && draftDrop ? (
								<Polyline
									positions={[draftPickup, draftDrop]}
									pathOptions={{ color: "#7b4dff", dashArray: "6 6", weight: 3 }}
								/>
							) : null}

							{selectedRideRoute.length > 0 ? (
								<Polyline positions={selectedRideRoute} pathOptions={{ color: "#ff7a4f", weight: 4 }} />
							) : null}
						</MapContainer>

						<div className="map-overlay">
							<div className="overlay-card">
								<div className="section-title">
									<strong>Map picker</strong>
									<span className="pill">
										{activeMapPicker === "ride"
											? `Hosting • ${ridePickTarget}`
											: `Booking • ${bookingPickTarget}`}
									</span>
								</div>
								<div className="chip-row">
									{draftStart ? <span className="pill success">Start pinned</span> : <span className="pill">Start</span>}
									{draftEnd ? <span className="pill">End pinned</span> : <span className="pill">End</span>}
									{draftPickup ? <span className="pill">Pickup set</span> : null}
									{draftDrop ? <span className="pill">Drop set</span> : null}
								</div>
							</div>
						</div>
					</div>
				</div>

				<p className="message">{message}</p>
			</div>
		);
	}
