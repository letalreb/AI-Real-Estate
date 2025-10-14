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

  return (
    <div className="filter-bar">
      <form onSubmit={handleSearchSubmit} className="search-form">
        <input
          type="text"
          placeholder="Cerca aste per parole chiave..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        <button type="submit" className="btn btn-primary">
          🔍 Cerca
        </button>
      </form>

      <div className="filters">
        <div className="filter-group">
          <label>Città</label>
          <input
            type="text"
            placeholder="es. Roma, Milano..."
            value={filters.city || ''}
            onChange={(e) => handleFilterChange('city', e.target.value)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>Tipo Immobile</label>
          <select
            value={filters.property_type || ''}
            onChange={(e) => handleFilterChange('property_type', e.target.value)}
            className="filter-select"
          >
            <option value="">Tutti</option>
            {Object.values(PropertyType).map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Prezzo Min (€)</label>
          <input
            type="number"
            placeholder="0"
            value={filters.min_price || ''}
            onChange={(e) => handleFilterChange('min_price', e.target.value ? Number(e.target.value) : undefined)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>Prezzo Max (€)</label>
          <input
            type="number"
            placeholder="1000000"
            value={filters.max_price || ''}
            onChange={(e) => handleFilterChange('max_price', e.target.value ? Number(e.target.value) : undefined)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>Score AI Min</label>
          <input
            type="number"
            placeholder="0"
            min="0"
            max="100"
            value={filters.min_score || ''}
            onChange={(e) => handleFilterChange('min_score', e.target.value ? Number(e.target.value) : undefined)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label>Stato</label>
          <select
            value={filters.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="filter-select"
          >
            <option value="">Tutti</option>
            <option value="upcoming">In arrivo</option>
            <option value="active">Attive</option>
            <option value="completed">Completate</option>
            <option value="cancelled">Annullate</option>
          </select>
        </div>

        <div className="filter-actions">
          <button onClick={handleReset} className="btn btn-secondary">
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};

export default FilterBar;
