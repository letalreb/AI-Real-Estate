import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Register.css';
import { register } from '../services/api';
import { User } from '../types';

interface RegisterProps {
  onRegister: (user: User, token: string) => void;
}

const Register: React.FC<RegisterProps> = ({ onRegister }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState<'weak' | 'medium' | 'strong' | null>(null);

  const calculatePasswordStrength = (password: string): 'weak' | 'medium' | 'strong' | null => {
    if (!password) return null;
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    if (strength <= 2) return 'weak';
    if (strength <= 3) return 'medium';
    return 'strong';
  };

  const handlePasswordChange = (password: string) => {
    setFormData({ ...formData, password });
    setPasswordStrength(calculatePasswordStrength(password));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.password !== formData.confirmPassword) {
      setError('Le password non corrispondono');
      return;
    }

    if (formData.password.length < 8) {
      setError('La password deve essere di almeno 8 caratteri');
      return;
    }

    setLoading(true);

    try {
      const response = await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || undefined,
      });
      onRegister(response.user, response.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore durante la registrazione');
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

          <h1>Crea Account</h1>
          <p className="auth-subtitle">
            Inizia a tracciare le migliori opportunità nelle aste immobiliari
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
              <label htmlFor="full_name">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                Nome Completo (Opzionale)
              </label>
              <input
                type="text"
                id="full_name"
                className="form-control"
                placeholder="Mario Rossi"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                autoComplete="name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
                Email *
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
                Password * (min 8 caratteri)
              </label>
              <input
                type="password"
                id="password"
                className="form-control"
                placeholder="Crea una password sicura"
                value={formData.password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
              {passwordStrength && (
                <div className="password-strength">
                  <div className="password-strength-bar">
                    <div className={`password-strength-fill ${passwordStrength}`}></div>
                  </div>
                  <div className={`password-strength-text ${passwordStrength}`}>
                    {passwordStrength === 'weak' && 'Password debole'}
                    {passwordStrength === 'medium' && 'Password media'}
                    {passwordStrength === 'strong' && 'Password forte'}
                  </div>
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Conferma Password *
              </label>
              <input
                type="password"
                id="confirmPassword"
                className="form-control"
                placeholder="Ripeti la password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>

            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? (
                <>
                  <div className="btn-spinner"></div>
                  <span>Registrazione in corso...</span>
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="8.5" cy="7" r="4" />
                    <line x1="20" y1="8" x2="20" y2="14" />
                    <line x1="23" y1="11" x2="17" y2="11" />
                  </svg>
                  <span>Crea Account</span>
                </>
              )}
            </button>
          </form>

          <div className="auth-divider">
            <span>oppure</span>
          </div>

          <p className="auth-footer">
            Hai già un account?{' '}
            <a href="/login">
              Accedi
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

export default Register;
