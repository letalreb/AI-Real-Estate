import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';
import { User } from '../types';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <Link to="/" className="logo">
            <div className="logo-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <path d="M16 3L3 12v17h10v-9h6v9h10V12L16 3z" fill="currentColor"/>
              </svg>
            </div>
            <div className="logo-text">
              <span className="logo-main">AI Real Estate</span>
              <span className="logo-sub">Aste Immobiliari</span>
            </div>
          </Link>

          {/* Mobile Menu Button */}
          <button 
            className={`mobile-menu-btn ${mobileMenuOpen ? 'active' : ''}`}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Menu"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>

          <nav className={`nav ${mobileMenuOpen ? 'mobile-open' : ''}`}>
            <Link 
              to="/" 
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M3 7l7-4 7 4v9H3V7z" stroke="currentColor" strokeWidth="2" fill="none"/>
              </svg>
              <span>Aste</span>
            </Link>
            
            <Link 
              to="/map" 
              className={`nav-link ${isActive('/map') ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="8" r="3" stroke="currentColor" strokeWidth="2" fill="none"/>
                <path d="M10 14c-4 0-7-3-7-6 0-3.5 3-6 7-6s7 2.5 7 6c0 3-3 6-7 6z" stroke="currentColor" strokeWidth="2" fill="none"/>
              </svg>
              <span>Mappa</span>
            </Link>
            
            {user ? (
              <>
                <Link 
                  to="/dashboard" 
                  className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <rect x="3" y="3" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="2" fill="none"/>
                    <rect x="11" y="3" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="2" fill="none"/>
                    <rect x="3" y="11" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="2" fill="none"/>
                    <rect x="11" y="11" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="2" fill="none"/>
                  </svg>
                  <span>Dashboard</span>
                </Link>
                
                <div className="user-menu">
                  <div className="user-avatar">
                    {user.email.charAt(0).toUpperCase()}
                  </div>
                  <div className="user-info">
                    <span className="user-email">{user.email}</span>
                    <button onClick={onLogout} className="btn-logout">
                      Esci
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="auth-buttons">
                <Link 
                  to="/login" 
                  className="btn btn-outline btn-sm"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Accedi
                </Link>
                <Link 
                  to="/register" 
                  className="btn btn-primary btn-sm"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Registrati
                </Link>
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
