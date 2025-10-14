import React, { useState, useEffect } from 'react';
import './SearchPreferences.css';
import { User, SearchPreference, CreateSearchPreferenceRequest, PropertyType } from '../types';
import { getPreferences, createPreference, updatePreference, deletePreference } from '../services/api';

interface SearchPreferencesProps {
  user: User;
}

const SearchPreferences: React.FC<SearchPreferencesProps> = ({ user }) => {
  const [preferences, setPreferences] = useState<SearchPreference[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState<CreateSearchPreferenceRequest>({
    name: '',
    filters: {},
    notification_enabled: true,
  });

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const data = await getPreferences();
      setPreferences(data);
    } catch (err: any) {
      setError('Errore nel caricamento delle preferenze');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      if (editingId) {
        await updatePreference(editingId, formData);
        setSuccess('Preferenza aggiornata con successo!');
      } else {
        await createPreference(formData);
        setSuccess('Preferenza creata con successo!');
      }
      resetForm();
      loadPreferences();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore nel salvare la preferenza');
    }
  };

  const handleEdit = (pref: SearchPreference) => {
    setEditingId(pref.id);
    setFormData({
      name: pref.name,
      filters: pref.filters,
      notification_enabled: pref.notification_enabled,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questa preferenza?')) {
      return;
    }

    try {
      await deletePreference(id);
      setSuccess('Preferenza eliminata con successo!');
      loadPreferences();
    } catch (err: any) {
      setError('Errore nell\'eliminazione della preferenza');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      filters: {},
      notification_enabled: true,
    });
    setEditingId(null);
    setShowForm(false);
  };

  const updateFilters = (key: string, value: any) => {
    setFormData({
      ...formData,
      filters: {
        ...formData.filters,
        [key]: value || undefined,
      },
    });
  };

  return (
    <div className="preferences-page">
      <div className="container">
        <div className="page-header">
          <h1>⭐ Preferenze di Ricerca</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="btn btn-primary"
          >
            {showForm ? 'Annulla' : '➕ Nuova Preferenza'}
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {showForm && (
          <div className="card form-card">
            <h2>{editingId ? 'Modifica Preferenza' : 'Nuova Preferenza'}</h2>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Nome Preferenza *</label>
                <input
                  type="text"
                  id="name"
                  className="form-control"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="es. Appartamenti Roma Centro"
                />
              </div>

              <div className="filters-grid">
                <div className="form-group">
                  <label htmlFor="city">Città</label>
                  <input
                    type="text"
                    id="city"
                    className="form-control"
                    value={formData.filters.city || ''}
                    onChange={(e) => updateFilters('city', e.target.value)}
                    placeholder="es. Roma, Milano"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="property_type">Tipo Immobile</label>
                  <select
                    id="property_type"
                    className="form-control"
                    value={formData.filters.property_type || ''}
                    onChange={(e) => updateFilters('property_type', e.target.value)}
                  >
                    <option value="">Tutti</option>
                    {Object.values(PropertyType).map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="min_price">Prezzo Min (€)</label>
                  <input
                    type="number"
                    id="min_price"
                    className="form-control"
                    value={formData.filters.min_price || ''}
                    onChange={(e) => updateFilters('min_price', e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="0"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="max_price">Prezzo Max (€)</label>
                  <input
                    type="number"
                    id="max_price"
                    className="form-control"
                    value={formData.filters.max_price || ''}
                    onChange={(e) => updateFilters('max_price', e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="1000000"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="min_score">Score AI Min</label>
                  <input
                    type="number"
                    id="min_score"
                    className="form-control"
                    value={formData.filters.min_score || ''}
                    onChange={(e) => updateFilters('min_score', e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="0"
                    min="0"
                    max="100"
                  />
                </div>

                <div className="form-group checkbox-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.notification_enabled}
                      onChange={(e) => setFormData({ ...formData, notification_enabled: e.target.checked })}
                    />
                    <span>Abilita Notifiche</span>
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button type="submit" className="btn btn-primary">
                  {editingId ? 'Aggiorna' : 'Salva'} Preferenza
                </button>
                <button type="button" onClick={resetForm} className="btn btn-secondary">
                  Annulla
                </button>
              </div>
            </form>
          </div>
        )}

        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Caricamento preferenze...</p>
          </div>
        ) : preferences.length === 0 ? (
          <div className="empty-state">
            <p className="empty-icon">📭</p>
            <h3>Nessuna preferenza salvata</h3>
            <p>Crea la tua prima preferenza di ricerca per ricevere notifiche</p>
          </div>
        ) : (
          <div className="preferences-grid">
            {preferences.map((pref) => (
              <div key={pref.id} className="preference-card">
                <div className="preference-header">
                  <h3>{pref.name}</h3>
                  {pref.notification_enabled && (
                    <span className="badge badge-success">🔔 Notifiche ON</span>
                  )}
                </div>

                <div className="preference-filters">
                  {pref.filters.city && (
                    <div className="filter-tag">
                      <span>📍 {pref.filters.city}</span>
                    </div>
                  )}
                  {pref.filters.property_type && (
                    <div className="filter-tag">
                      <span>🏠 {pref.filters.property_type}</span>
                    </div>
                  )}
                  {pref.filters.min_price && (
                    <div className="filter-tag">
                      <span>
                        💰 Min: {new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(pref.filters.min_price)}
                      </span>
                    </div>
                  )}
                  {pref.filters.max_price && (
                    <div className="filter-tag">
                      <span>
                        💰 Max: {new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(pref.filters.max_price)}
                      </span>
                    </div>
                  )}
                  {pref.filters.min_score && (
                    <div className="filter-tag">
                      <span>⭐ Score Min: {pref.filters.min_score}</span>
                    </div>
                  )}
                </div>

                <div className="preference-actions">
                  <button onClick={() => handleEdit(pref)} className="btn btn-outline btn-sm">
                    ✏️ Modifica
                  </button>
                  <button onClick={() => handleDelete(pref.id)} className="btn btn-danger btn-sm">
                    🗑️ Elimina
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPreferences;
