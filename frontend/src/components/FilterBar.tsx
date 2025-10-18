import React, { ChangeEvent } from 'react';
import './FilterBar.css';
import { PropertyType, AuctionStatus } from '../types';

interface FilterBarProps {
  filters: {
    city?: string;
    property_type?: PropertyType;
    min_price?: number;
    max_price?: number;
    min_score?: number;
    status?: AuctionStatus;
  };
  onFilterChange: (filters: any) => void;
  onSearch: (query: string) => void;
}

const FilterBar: React.FC<FilterBarProps> = ({ filters, onFilterChange, onSearch }) => {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [isExpanded, setIsExpanded] = React.useState(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onSearch(searchQuery.trim());
    }
  };

  const handleFilterChange = (key: string, value: any) => {
    onFilterChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const handleReset = () => {
    setSearchQuery('');
    onFilterChange({});
  };

  const hasActiveFilters = Object.values(filters).some(value => value !== undefined && value !== '');

  return (
    <div className="filter-bar">
      <div className="filter-bar-header">
        <form onSubmit={handleSearchSubmit} className="search-form">
          <div className="search-input-wrapper">
            <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <input
              type="text"
              placeholder="Cerca aste per parole chiave..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
          <button type="submit" className="btn btn-primary search-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <span>Cerca</span>
          </button>
        </form>

        <button 
          className={`toggle-filters-btn ${isExpanded ? 'active' : ''}`}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
          <span>Filtri</span>
          {hasActiveFilters && <span className="filter-badge">{Object.values(filters).filter(v => v).length}</span>}
          <svg className={`chevron ${isExpanded ? 'up' : 'down'}`} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      </div>

      <div className={`filters ${isExpanded ? 'expanded' : ''}`}>
        <div className="filter-group">
          <label>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            Città
          </label>
          <input
            type="text"
            placeholder="es. Roma, Milano..."
            value={filters.city || ''}
            onChange={(e) => handleFilterChange('city', e.target.value)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
            Tipo Immobile
          </label>
          <select
            value={filters.property_type || ''}
            onChange={(e) => handleFilterChange('property_type', e.target.value)}
            className="filter-select"
          >
            <option value="">Tutti i tipi</option>
            {Object.values(PropertyType).map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="1" x2="12" y2="23" />
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
            Prezzo Min (€)
          </label>
          <input
            type="number"
            placeholder="0"
            value={filters.min_price || ''}
            onChange={(e) => handleFilterChange('min_price', e.target.value ? Number(e.target.value) : undefined)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="1" x2="12" y2="23" />
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
            Prezzo Max (€)
          </label>
          <input
            type="number"
            placeholder="1.000.000"
            value={filters.max_price || ''}
            onChange={(e) => handleFilterChange('max_price', e.target.value ? Number(e.target.value) : undefined)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            Score AI Min
          </label>
          <input
            type="number"
            placeholder="0-100"
            min="0"
            max="100"
            value={filters.min_score || ''}
            onChange={(e) => handleFilterChange('min_score', e.target.value ? Number(e.target.value) : undefined)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            Stato
          </label>
          <select
            value={filters.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="filter-select"
          >
            <option value="">Tutti gli stati</option>
            <option value="upcoming">In arrivo</option>
            <option value="active">Attive</option>
            <option value="completed">Completate</option>
            <option value="cancelled">Annullate</option>
          </select>
        </div>

        <div className="filter-actions">
          <button onClick={handleReset} className="btn btn-reset" disabled={!hasActiveFilters}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10" />
              <polyline points="23 20 23 14 17 14" />
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
            </svg>
            <span>Reset</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default FilterBar;
