import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Dashboard.css';
import { User, Notification } from '../types';
import { getNotifications, markNotificationRead } from '../services/api';
import wsService from '../services/websocket';

interface DashboardProps {
  user: User;
}

const Dashboard: React.FC<DashboardProps> = ({ user }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
    
    // Connect WebSocket
    const token = localStorage.getItem('token');
    if (token) {
      wsService.connect(token);
      
      // Subscribe to notifications
      const unsubscribe = wsService.subscribe('notification', (data: Notification) => {
        setNotifications((prev) => [data, ...prev]);
      });

      return () => {
        unsubscribe();
      };
    }
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await getNotifications(0, 10);
      setNotifications(response.items);
    } catch (error) {
      console.error('Error loading notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id: number) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="dashboard-page">
      <div className="container">
        <div className="dashboard-header">
          <div className="header-text">
            <h1>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              Benvenuto, {user.full_name || user.email}!
            </h1>
            <p className="dashboard-subtitle">
              Gestisci le tue preferenze di ricerca e visualizza le notifiche
            </p>
          </div>
        </div>

        <div className="dashboard-grid">
          {/* Quick Stats */}
          <div className="card stats-card">
            <div className="card-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="20" x2="12" y2="10" />
                <line x1="18" y1="20" x2="18" y2="4" />
                <line x1="6" y1="20" x2="6" y2="16" />
              </svg>
            </div>
            <h2>Statistiche</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                </div>
                <div className="stat-content">
                  <div className="stat-value">{unreadCount}</div>
                  <div className="stat-label">Notifiche Non Lette</div>
                </div>
              </div>
              <div className="stat-item">
                <div className="stat-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                </div>
                <div className="stat-content">
                  <div className="stat-value">{notifications.length}</div>
                  <div className="stat-label">Totale Notifiche</div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card actions-card">
            <div className="card-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <h2>Azioni Rapide</h2>
            <div className="actions-grid">
              <Link to="/preferences" className="action-btn">
                <div className="action-icon">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                  </svg>
                </div>
                <span className="action-text">Gestisci Preferenze</span>
              </Link>
              <Link to="/" className="action-btn">
                <div className="action-icon">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.35-4.35" />
                  </svg>
                </div>
                <span className="action-text">Cerca Aste</span>
              </Link>
              <Link to="/map" className="action-btn">
                <div className="action-icon">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
                    <line x1="8" y1="2" x2="8" y2="18" />
                    <line x1="16" y1="6" x2="16" y2="22" />
                  </svg>
                </div>
                <span className="action-text">Visualizza Mappa</span>
              </Link>
            </div>
          </div>

          {/* Notifications */}
          <div className="card notifications-card">
            <div className="card-header">
              <div className="header-left">
                <div className="card-icon">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                </div>
                <h2>Notifiche Recenti</h2>
              </div>
              {unreadCount > 0 && (
                <span className="notification-badge">{unreadCount}</span>
              )}
            </div>

            {loading ? (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>Caricamento notifiche...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                </div>
                <p>Nessuna notifica al momento</p>
              </div>
            ) : (
              <div className="notifications-list">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}
                  >
                    <div className="notification-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="16" x2="12" y2="12" />
                        <line x1="12" y1="8" x2="12.01" y2="8" />
                      </svg>
                    </div>
                    <div className="notification-content">
                      <p>{notification.message}</p>
                      <span className="notification-date">
                        {new Date(notification.created_at).toLocaleString('it-IT')}
                      </span>
                    </div>
                    {!notification.is_read && (
                      <button
                        onClick={() => handleMarkRead(notification.id)}
                        className="btn btn-mark-read"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        <span>Letto</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
