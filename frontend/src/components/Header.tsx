import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';
import { User } from '../types';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <Link to="/" className="logo">
            <span className="logo-icon">🏠</span>
            <span className="logo-text">AI Auction Analyzer</span>
          </Link>

          <nav className="nav">
            <Link to="/" className="nav-link">Aste</Link>
            <Link to="/map" className="nav-link">Mappa</Link>
            
            {user ? (
              <>
                <Link to="/dashboard" className="nav-link">Dashboard</Link>
                <Link to="/preferences" className="nav-link">Preferenze</Link>
                <div className="user-menu">
                  <span className="user-email">{user.email}</span>
                  <button onClick={onLogout} className="btn btn-secondary btn-sm">
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <div className="auth-buttons">
                <Link to="/login" className="btn btn-outline btn-sm">Login</Link>
                <Link to="/register" className="btn btn-primary btn-sm">Registrati</Link>
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
