import React, { useState, useEffect } from 'react';
import './AuctionList.css';
import FilterBar from '../components/FilterBar';
import AuctionCard from '../components/AuctionCard';
import { getAuctions, searchAuctionsText } from '../services/api';
import { Auction, AuctionFilters } from '../types';

const AuctionList: React.FC = () => {
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AuctionFilters>({ skip: 0, limit: 20 });
  const [total, setTotal] = useState(0);
  const [searchMode, setSearchMode] = useState(false);

  useEffect(() => {
    loadAuctions();
  }, [filters]);

  const loadAuctions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getAuctions(filters);
      setAuctions(response.items);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento delle aste');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters: AuctionFilters) => {
    setFilters({ ...newFilters, skip: 0, limit: 20 });
    setSearchMode(false);
  };

  const handleSearch = async (query: string) => {
    try {
      setLoading(true);
      setError(null);
      setSearchMode(true);
      const response = await searchAuctionsText(query);
      setAuctions(response.items);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || 'Errore nella ricerca');
    } finally {
      setLoading(false);
    }
  };

  const loadMore = async () => {
    try {
      const newFilters = { ...filters, skip: auctions.length };
      const response = await getAuctions(newFilters);
      setAuctions([...auctions, ...response.items]);
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento');
    }
  };

  return (
    <div className="auction-list-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 2l2 6h6l-5 4 2 6-5-4-5 4 2-6-5-4h6l2-6z" fill="currentColor"/>
              </svg>
              <span>Powered by AI</span>
            </div>
            <h1 className="hero-title">
              Trova le <span className="gradient-text">Migliori Occasioni</span>
              <br />nelle Aste Immobiliari
            </h1>
            <p className="hero-subtitle">
              Intelligenza artificiale che analizza migliaia di aste giudiziarie italiane 
              per aiutarti a trovare l'investimento perfetto
            </p>
            <div className="hero-stats">
              <div className="stat-item">
                <div className="stat-value">{total.toLocaleString('it-IT')}</div>
                <div className="stat-label">Aste Disponibili</div>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-item">
                <div className="stat-value">24/7</div>
                <div className="stat-label">Monitoraggio</div>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-item">
                <div className="stat-value">AI</div>
                <div className="stat-label">Score Intelligente</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Filter Bar */}
      <section className="filter-section">
        <div className="container">
          <FilterBar 
            filters={filters}
            onFilterChange={handleFilterChange} 
            onSearch={handleSearch}
          />
        </div>
      </section>

      {/* Auctions Grid */}
      <section className="auctions-section">
        <div className="container">
          {error && (
            <div className="alert alert-error">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="2" fill="none"/>
                <path d="M10 6v4M10 14h.01" stroke="currentColor" strokeWidth="2"/>
              </svg>
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="loading-grid">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="skeleton-card">
                  <div className="skeleton-image"></div>
                  <div className="skeleton-content">
                    <div className="skeleton-title"></div>
                    <div className="skeleton-text"></div>
                    <div className="skeleton-text short"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : auctions.length > 0 ? (
            <>
              <div className="auctions-header">
                <h2 className="section-title">
                  {searchMode ? 'Risultati della Ricerca' : 'Aste Disponibili'}
                </h2>
                <span className="results-count">
                  {total.toLocaleString('it-IT')} {total === 1 ? 'risultato' : 'risultati'}
                </span>
              </div>
              
              <div className="auctions-grid">
                {auctions.map((auction) => (
                  <AuctionCard key={auction.id} auction={auction} />
                ))}
              </div>

              {auctions.length < total && !searchMode && (
                <div className="load-more-container">
                  <button onClick={loadMore} className="btn btn-outline btn-lg">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <path d="M10 4v12M4 10h12" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                    <span>Carica Altre Aste</span>
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <rect x="12" y="20" width="40" height="32" rx="2" stroke="currentColor" strokeWidth="3" fill="none"/>
                  <path d="M22 20V16a6 6 0 0112 0v4" stroke="currentColor" strokeWidth="3"/>
                  <circle cx="32" cy="36" r="3" fill="currentColor"/>
                </svg>
              </div>
              <h3 className="empty-title">Nessuna asta trovata</h3>
              <p className="empty-text">
                {searchMode 
                  ? 'Prova a modificare i criteri di ricerca o usa filtri diversi'
                  : 'Al momento non ci sono aste disponibili con questi filtri'
                }
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default AuctionList;
