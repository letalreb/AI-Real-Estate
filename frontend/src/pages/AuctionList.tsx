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

  const handleLoadMore = () => {
    setFilters((prev) => ({ ...prev, skip: (prev.skip || 0) + (prev.limit || 20) }));
  };

  const hasMore = (filters.skip || 0) + auctions.length < total;

  return (
    <div className="auction-list-page">
      <div className="container">
        <div className="page-header">
          <h1>🏠 Aste Immobiliari</h1>
          <p className="page-subtitle">
            {searchMode 
              ? `${total} risultat${total === 1 ? 'o' : 'i'} trovati`
              : `${total} aste disponibili`}
          </p>
        </div>

        <FilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onSearch={handleSearch}
        />

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {loading && auctions.length === 0 ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Caricamento aste in corso...</p>
          </div>
        ) : auctions.length === 0 ? (
          <div className="empty-state">
            <p className="empty-icon">🔍</p>
            <h3>Nessuna asta trovata</h3>
            <p>Prova a modificare i filtri di ricerca</p>
          </div>
        ) : (
          <>
            <div className="auction-grid">
              {auctions.map((auction) => (
                <AuctionCard key={auction.id} auction={auction} />
              ))}
            </div>

            {hasMore && (
              <div className="load-more-container">
                <button
                  onClick={handleLoadMore}
                  disabled={loading}
                  className="btn btn-primary btn-lg"
                >
                  {loading ? 'Caricamento...' : 'Carica altre aste'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AuctionList;
