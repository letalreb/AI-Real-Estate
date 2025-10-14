import axios, { AxiosInstance } from 'axios';
import {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  Auction,
  AuctionFilters,
  PaginatedResponse,
  SearchPreference,
  CreateSearchPreferenceRequest,
  Notification,
  MarketStats
} from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle 401 errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(data: LoginRequest): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append('username', data.email);
    formData.append('password', data.password);
    
    const response = await this.client.post<AuthResponse>('/users/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/users/register', data);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/users/me');
    return response.data;
  }

  // Auction endpoints
  async getAuctions(filters?: AuctionFilters): Promise<PaginatedResponse<Auction>> {
    const response = await this.client.get<PaginatedResponse<Auction>>('/auctions', {
      params: filters,
    });
    return response.data;
  }

  async getAuction(id: number): Promise<Auction> {
    const response = await this.client.get<Auction>(`/auctions/${id}`);
    return response.data;
  }

  async searchAuctionsText(query: string, skip = 0, limit = 20): Promise<PaginatedResponse<Auction>> {
    const response = await this.client.get<PaginatedResponse<Auction>>('/auctions/search/text', {
      params: { q: query, skip, limit },
    });
    return response.data;
  }

  async searchAuctionsNearby(
    latitude: number,
    longitude: number,
    radius_km: number,
    skip = 0,
    limit = 20
  ): Promise<PaginatedResponse<Auction>> {
    const response = await this.client.get<PaginatedResponse<Auction>>('/auctions/search/nearby', {
      params: { latitude, longitude, radius_km, skip, limit },
    });
    return response.data;
  }

  async getMarketStats(city?: string): Promise<MarketStats> {
    const response = await this.client.get<MarketStats>('/auctions/stats', {
      params: city ? { city } : {},
    });
    return response.data;
  }

  // Search Preferences endpoints
  async getPreferences(): Promise<SearchPreference[]> {
    const response = await this.client.get<SearchPreference[]>('/preferences');
    return response.data;
  }

  async createPreference(data: CreateSearchPreferenceRequest): Promise<SearchPreference> {
    const response = await this.client.post<SearchPreference>('/preferences', data);
    return response.data;
  }

  async updatePreference(id: number, data: Partial<CreateSearchPreferenceRequest>): Promise<SearchPreference> {
    const response = await this.client.put<SearchPreference>(`/preferences/${id}`, data);
    return response.data;
  }

  async deletePreference(id: number): Promise<void> {
    await this.client.delete(`/preferences/${id}`);
  }

  // Notification endpoints
  async getNotifications(skip = 0, limit = 20): Promise<PaginatedResponse<Notification>> {
    const response = await this.client.get<PaginatedResponse<Notification>>('/notifications', {
      params: { skip, limit },
    });
    return response.data;
  }

  async markNotificationRead(id: number): Promise<Notification> {
    const response = await this.client.put<Notification>(`/notifications/${id}/read`);
    return response.data;
  }
}

const api = new ApiClient();

// Export individual functions
export const login = (data: LoginRequest) => api.login(data);
export const register = (data: RegisterRequest) => api.register(data);
export const getCurrentUser = () => api.getCurrentUser();

export const getAuctions = (filters?: AuctionFilters) => api.getAuctions(filters);
export const getAuction = (id: number) => api.getAuction(id);
export const searchAuctionsText = (query: string, skip?: number, limit?: number) => 
  api.searchAuctionsText(query, skip, limit);
export const searchAuctionsNearby = (lat: number, lng: number, radius: number, skip?: number, limit?: number) => 
  api.searchAuctionsNearby(lat, lng, radius, skip, limit);
export const getMarketStats = (city?: string) => api.getMarketStats(city);

export const getPreferences = () => api.getPreferences();
export const createPreference = (data: CreateSearchPreferenceRequest) => api.createPreference(data);
export const updatePreference = (id: number, data: Partial<CreateSearchPreferenceRequest>) => 
  api.updatePreference(id, data);
export const deletePreference = (id: number) => api.deletePreference(id);

export const getNotifications = (skip?: number, limit?: number) => api.getNotifications(skip, limit);
export const markNotificationRead = (id: number) => api.markNotificationRead(id);

export default api;
