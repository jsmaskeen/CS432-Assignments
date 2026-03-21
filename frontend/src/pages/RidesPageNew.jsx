import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import { api } from '../api';

export default function RidesPageNew() {
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
            <Link to="/" className="btn ghost">Home</Link>
            <Link to="/auth" className="btn primary">Login / Switch</Link>
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
