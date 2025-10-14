import React from 'react';
import { Link } from 'react-router-dom';
import './AuctionCard.css';
import { Auction } from '../types';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

interface AuctionCardProps {
  auction: Auction;
}

const AuctionCard: React.FC<AuctionCardProps> = ({ auction }) => {
  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#28a745';
    if (score >= 60) return '#ffc107';
    if (score >= 40) return '#fd7e14';
    return '#dc3545';
  };

  const getStatusBadge = (status: string): string => {
    switch (status) {
      case 'active':
        return 'badge-success';
      case 'upcoming':
        return 'badge-info';
      case 'completed':
        return 'badge-warning';
      case 'cancelled':
        return 'badge-danger';
      default:
        return 'badge-info';
    }
  };

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case 'active':
        return 'Attiva';
      case 'upcoming':
        return 'In arrivo';
      case 'completed':
        return 'Completata';
      case 'cancelled':
        return 'Annullata';
      default:
        return status;
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
      return format(new Date(dateString), 'dd MMMM yyyy', { locale: it });
    } catch {
      return 'Data non valida';
    }
  };

  return (
    <div className="auction-card">
      <div className="auction-header">
        <div className="auction-badges">
          <span className={`badge ${getStatusBadge(auction.auction_status)}`}>
            {getStatusLabel(auction.auction_status)}
          </span>
          <span className="badge badge-info">{auction.property_type}</span>
        </div>
        <div 
          className="auction-score" 
          style={{ backgroundColor: getScoreColor(auction.ai_score) }}
        >
          <span className="score-value">{auction.ai_score}</span>
          <span className="score-label">AI Score</span>
        </div>
      </div>

      <Link to={`/auctions/${auction.id}`} className="auction-link">
        <h3 className="auction-title">{auction.title}</h3>
      </Link>

      <div className="auction-details">
        <div className="detail-item">
          <span className="detail-icon">📍</span>
          <span className="detail-text">{auction.city}</span>
        </div>

        {auction.surface_sqm && (
          <div className="detail-item">
            <span className="detail-icon">📐</span>
            <span className="detail-text">{auction.surface_sqm} m²</span>
          </div>
        )}

        {auction.rooms && (
          <div className="detail-item">
            <span className="detail-icon">🚪</span>
            <span className="detail-text">{auction.rooms} locali</span>
          </div>
        )}

        {auction.auction_date && (
          <div className="detail-item">
            <span className="detail-icon">📅</span>
            <span className="detail-text">{formatDate(auction.auction_date)}</span>
          </div>
        )}
      </div>

      <div className="auction-prices">
        <div className="price-item">
          <span className="price-label">Prezzo Base</span>
          <span className="price-value">{formatPrice(auction.base_price)}</span>
        </div>

        {auction.estimated_value && (
          <div className="price-item">
            <span className="price-label">Valore Stimato</span>
            <span className="price-value estimated">{formatPrice(auction.estimated_value)}</span>
          </div>
        )}
      </div>

      {auction.estimated_value && (
        <div className="auction-discount">
          <span className="discount-label">Sconto potenziale:</span>
          <span className="discount-value">
            {Math.round((1 - auction.base_price / auction.estimated_value) * 100)}%
          </span>
        </div>
      )}

      <Link to={`/auctions/${auction.id}`} className="btn btn-primary btn-full">
        Vedi Dettagli
      </Link>
    </div>
  );
};

export default AuctionCard;
