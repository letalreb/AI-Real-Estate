import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import './AuctionDetail.css';
import { getAuction } from '../services/api';
import { Auction } from '../types';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

const AuctionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [auction, setAuction] = useState<Auction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadAuction(Number(id));
    }
  }, [id]);

  const loadAuction = async (auctionId: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAuction(auctionId);
      setAuction(data);
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento dell\'asta');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Data non disponibile';
    try {
      return format(new Date(dateString), 'dd MMMM yyyy, HH:mm', { locale: it });
    } catch {
      return 'Data non valida';
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#28a745';
    if (score >= 60) return '#ffc107';
    if (score >= 40) return '#fd7e14';
    return '#dc3545';
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Caricamento dettagli asta...</p>
      </div>
    );
  }

  if (error || !auction) {
    return (
      <div className="container">
        <div className="alert alert-error">
          {error || 'Asta non trovata'}
        </div>
        <Link to="/" className="btn btn-primary">
          Torna alle aste
        </Link>
      </div>
    );
  }

  return (
    <div className="auction-detail-page">
      <div className="container">
        <Link to="/" className="back-link">
          ← Torna alle aste
        </Link>

        <div className="detail-header">
          <div className="header-content">
            <h1>{auction.title}</h1>
            <div className="header-badges">
              <span className="badge badge-info">{auction.property_type}</span>
              <span className="badge badge-success">{auction.auction_status}</span>
            </div>
          </div>
          
          <div 
            className="detail-score"
            style={{ backgroundColor: getScoreColor(auction.ai_score) }}
          >
            <div className="score-number">{auction.ai_score}</div>
            <div className="score-text">AI Score</div>
          </div>
        </div>

        <div className="detail-grid">
          {/* Main Info */}
          <div className="detail-section main-info">
            <h2>📋 Informazioni Principali</h2>
            
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">📍 Città</span>
                <span className="info-value">{auction.city}</span>
              </div>

              {auction.address && (
                <div className="info-item">
                  <span className="info-label">🏠 Indirizzo</span>
                  <span className="info-value">{auction.address}</span>
                </div>
              )}

              {auction.surface_sqm && (
                <div className="info-item">
                  <span className="info-label">📐 Superficie</span>
                  <span className="info-value">{auction.surface_sqm} m²</span>
                </div>
              )}

              {auction.rooms && (
                <div className="info-item">
                  <span className="info-label">🚪 Locali</span>
                  <span className="info-value">{auction.rooms}</span>
                </div>
              )}

              {auction.court_name && (
                <div className="info-item">
                  <span className="info-label">⚖️ Tribunale</span>
                  <span className="info-value">{auction.court_name}</span>
                </div>
              )}

              {auction.procedure_number && (
                <div className="info-item">
                  <span className="info-label">📄 N. Procedura</span>
                  <span className="info-value">{auction.procedure_number}</span>
                </div>
              )}

              {auction.auction_date && (
                <div className="info-item">
                  <span className="info-label">📅 Data Asta</span>
                  <span className="info-value">{formatDate(auction.auction_date)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Price Info */}
          <div className="detail-section price-info">
            <h2>💰 Informazioni Economiche</h2>
            
            <div className="price-cards">
              <div className="price-card">
                <div className="price-card-label">Prezzo Base</div>
                <div className="price-card-value">{formatPrice(auction.base_price)}</div>
              </div>

              {auction.current_price && (
                <div className="price-card">
                  <div className="price-card-label">Prezzo Attuale</div>
                  <div className="price-card-value current">{formatPrice(auction.current_price)}</div>
                </div>
              )}

              {auction.estimated_value && (
                <div className="price-card">
                  <div className="price-card-label">Valore Stimato</div>
                  <div className="price-card-value estimated">{formatPrice(auction.estimated_value)}</div>
                </div>
              )}
            </div>

            {auction.estimated_value && (
              <div className="discount-highlight">
                <span className="discount-label">Sconto Potenziale</span>
                <span className="discount-value">
                  {Math.round((1 - auction.base_price / auction.estimated_value) * 100)}%
                </span>
              </div>
            )}
          </div>

          {/* Description */}
          <div className="detail-section description">
            <h2>📝 Descrizione</h2>
            <p>{auction.description || 'Nessuna descrizione disponibile'}</p>
          </div>

          {/* Map */}
          {auction.latitude && auction.longitude && (
            <div className="detail-section map-section">
              <h2>🗺️ Posizione</h2>
              <div className="map-placeholder">
                <p>Coordinate: {auction.latitude.toFixed(6)}, {auction.longitude.toFixed(6)}</p>
                <Link to={`/map?lat=${auction.latitude}&lng=${auction.longitude}`} className="btn btn-primary">
                  Visualizza sulla Mappa
                </Link>
              </div>
            </div>
          )}

          {/* Source Link */}
          <div className="detail-section source-link">
            <h2>🔗 Fonte</h2>
            <a 
              href={auction.source_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="btn btn-outline"
            >
              Visualizza Annuncio Originale ↗
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuctionDetail;
