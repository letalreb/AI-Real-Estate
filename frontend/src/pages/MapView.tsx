import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Link, useSearchParams } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';
import { getAuctions } from '../services/api';
import { Auction } from '../types';

// Import marker icons
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Fix for default marker icons in Leaflet with Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const MapView: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [loading, setLoading] = useState(true);
  const [center, setCenter] = useState<[number, number]>([41.9028, 12.4964]); // Rome default

  useEffect(() => {
    // Check if coordinates are provided in URL
    const lat = searchParams.get('lat');
    const lng = searchParams.get('lng');
    if (lat && lng) {
      setCenter([parseFloat(lat), parseFloat(lng)]);
    }

    loadAuctions();
  }, [searchParams]);

  const loadAuctions = async () => {
    try {
      setLoading(true);
      const response = await getAuctions({ limit: 1000 }); // Load all auctions with coordinates
      const auctionsWithCoords = response.items.filter(
        (a) => a.latitude !== null && a.longitude !== null
      );
      setAuctions(auctionsWithCoords);
    } catch (error) {
      console.error('Error loading auctions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMarkerColor = (score: number): string => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'orange';
    return 'red';
  };

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="map-view-page">
      <div className="map-header">
        <div className="container">
          <h1>🗺️ Mappa delle Aste</h1>
          <p>{auctions.length} aste visualizzate sulla mappa</p>
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Caricamento mappa...</p>
        </div>
      ) : (
        <MapContainer
          center={center}
          zoom={6}
          className="map-container"
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {auctions.map((auction) => (
            <Marker
              key={auction.id}
              position={[auction.latitude!, auction.longitude!]}
            >
              <Popup>
                <div className="map-popup">
                  <h3>{auction.title}</h3>
                  <div className="popup-details">
                    <p>
                      <strong>📍</strong> {auction.city}
                    </p>
                    <p>
                      <strong>🏠</strong> {auction.property_type}
                    </p>
                    <p>
                      <strong>💰</strong> {formatPrice(auction.base_price)}
                    </p>
                    <p>
                      <strong>⭐</strong> AI Score: {auction.ai_score}
                    </p>
                  </div>
                  <Link to={`/auctions/${auction.id}`} className="btn btn-primary btn-sm">
                    Vedi Dettagli
                  </Link>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      )}

      <div className="map-legend">
        <div className="container">
          <h3>Legenda Score AI</h3>
          <div className="legend-items">
            <div className="legend-item">
              <span className="legend-marker green"></span>
              <span>Score Alto (80+)</span>
            </div>
            <div className="legend-item">
              <span className="legend-marker orange"></span>
              <span>Score Medio (60-79)</span>
            </div>
            <div className="legend-item">
              <span className="legend-marker red"></span>
              <span>Score Basso (&lt;60)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;
