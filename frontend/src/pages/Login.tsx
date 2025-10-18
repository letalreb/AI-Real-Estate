import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';
import { login } from '../services/api';
import { User } from '../types';

interface LoginProps {
  onLogin: (user: User, token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await login(formData);
      onLogin(response.user, response.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore durante il login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-logo">
            <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
              <path d="M16 3L3 12v17h10v-9h6v9h10V12L16 3z" fill="url(#logo-gradient)" />
              <defs>
                <linearGradient id="logo-gradient" x1="3" y1="3" x2="29" y2="29">
                  <stop offset="0%" stopColor="#2563eb" />
                  <stop offset="100%" stopColor="#059669" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <h1>Benvenuto</h1>
          <p className="auth-subtitle">
            Accedi per gestire le tue preferenze di ricerca
          </p>

          {error && (
            <div className="alert alert-error">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
                Email
              </label>
              <input
                type="email"
                id="email"
                className="form-control"
                placeholder="nome@esempio.it"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                Password
              </label>
              <input
                type="password"
                id="password"
                className="form-control"
                placeholder="Inserisci la tua password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                autoComplete="current-password"
              />
            </div>

            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? (
                <>
                  <div className="btn-spinner"></div>
                  <span>Accesso in corso...</span>
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                    <polyline points="10 17 15 12 10 7" />
                    <line x1="15" y1="12" x2="3" y2="12" />
                  </svg>
                  <span>Accedi</span>
                </>
              )}
            </button>
          </form>

          <div className="auth-divider">
            <span>oppure</span>
          </div>

          <p className="auth-footer">
            Non hai un account?{' '}
            <a href="/register">
              Registrati gratuitamente
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
