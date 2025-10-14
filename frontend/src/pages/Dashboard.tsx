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
          <div>
            <h1>👋 Benvenuto, {user.full_name || user.email}!</h1>
            <p className="dashboard-subtitle">
              Gestisci le tue preferenze di ricerca e visualizza le notifiche
            </p>
          </div>
        </div>

        <div className="dashboard-grid">
          {/* Quick Stats */}
          <div className="card stats-card">
            <h2>📊 Statistiche</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{unreadCount}</div>
                <div className="stat-label">Notifiche Non Lette</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{notifications.length}</div>
                <div className="stat-label">Totale Notifiche</div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card actions-card">
            <h2>⚡ Azioni Rapide</h2>
            <div className="actions-grid">
              <Link to="/preferences" className="action-btn">
                <span className="action-icon">⭐</span>
                <span className="action-text">Gestisci Preferenze</span>
              </Link>
              <Link to="/" className="action-btn">
                <span className="action-icon">🔍</span>
                <span className="action-text">Cerca Aste</span>
              </Link>
              <Link to="/map" className="action-btn">
                <span className="action-icon">🗺️</span>
                <span className="action-text">Visualizza Mappa</span>
              </Link>
            </div>
          </div>

          {/* Notifications */}
          <div className="card notifications-card">
            <div className="card-header">
              <h2>🔔 Notifiche Recenti</h2>
              {unreadCount > 0 && (
                <span className="badge badge-danger">{unreadCount} nuove</span>
              )}
            </div>

            {loading ? (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>Caricamento notifiche...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="empty-state">
                <p>📭 Nessuna notifica al momento</p>
              </div>
            ) : (
              <div className="notifications-list">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}
                  >
                    <div className="notification-content">
                      <p>{notification.message}</p>
                      <span className="notification-date">
                        {new Date(notification.created_at).toLocaleString('it-IT')}
                      </span>
                    </div>
                    {!notification.is_read && (
                      <button
                        onClick={() => handleMarkRead(notification.id)}
                        className="btn btn-sm btn-outline"
                      >
                        Segna come letto
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
