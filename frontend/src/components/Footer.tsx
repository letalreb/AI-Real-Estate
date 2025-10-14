import React from 'react';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <div className="footer-section">
            <h3>AI Real Estate Auction Analyzer</h3>
            <p>Analizza le aste immobiliari con intelligenza artificiale</p>
          </div>

          <div className="footer-section">
            <h4>Link Utili</h4>
            <ul>
              <li><a href="https://pvp.giustizia.it" target="_blank" rel="noopener noreferrer">
                Portale Vendite Pubbliche
              </a></li>
              <li><a href="/docs/api-spec.yaml" target="_blank" rel="noopener noreferrer">
                API Documentation
              </a></li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Informazioni Legali</h4>
            <ul>
              <li><a href="/LEGAL.md" target="_blank" rel="noopener noreferrer">
                Note Legali
              </a></li>
              <li><a href="/LICENSE" target="_blank" rel="noopener noreferrer">
                Licenza
              </a></li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Contatti</h4>
            <p>Per supporto tecnico o segnalazioni:</p>
            <p>Email: <a href="mailto:support@example.com">support@example.com</a></p>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} AI Real Estate Auction Analyzer. MIT License.</p>
          <p className="disclaimer">
            Questo sistema rispetta robots.txt e le linee guida etiche per il web scraping.
            I dati sono raccolti da fonti pubbliche secondo le normative vigenti.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
