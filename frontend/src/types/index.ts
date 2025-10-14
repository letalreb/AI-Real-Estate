// User types
export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Auction types
export interface Auction {
  id: number;
  title: string;
  description: string;
  property_type: PropertyType;
  city: string;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  base_price: number;
  current_price: number | null;
  estimated_value: number | null;
  surface_sqm: number | null;
  rooms: number | null;
  auction_date: string | null;
  auction_status: AuctionStatus;
  court_name: string | null;
  procedure_number: string | null;
  ai_score: number;
  source_url: string;
  raw_text: string;
  created_at: string;
  updated_at: string;
}

export enum PropertyType {
  APPARTAMENTO = 'Appartamento',
  VILLA = 'Villa',
  TERRENO = 'Terreno',
  UFFICIO = 'Ufficio',
  NEGOZIO = 'Negozio',
  CAPANNONE = 'Capannone',
  BOX = 'Box',
  CANTINA = 'Cantina',
  ALTRO = 'Altro'
}

export enum AuctionStatus {
  UPCOMING = 'upcoming',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export interface AuctionFilters {
  city?: string;
  property_type?: PropertyType;
  min_price?: number;
  max_price?: number;
  min_score?: number;
  status?: AuctionStatus;
  skip?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// Search Preference types
export interface SearchPreference {
  id: number;
  user_id: number;
  name: string;
  filters: {
    city?: string;
    property_type?: PropertyType;
    min_price?: number;
    max_price?: number;
    min_score?: number;
  };
  notification_enabled: boolean;
  created_at: string;
}

export interface CreateSearchPreferenceRequest {
  name: string;
  filters: {
    city?: string;
    property_type?: PropertyType;
    min_price?: number;
    max_price?: number;
    min_score?: number;
  };
  notification_enabled?: boolean;
}

// Notification types
export interface Notification {
  id: number;
  user_id: number;
  auction_id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

// WebSocket types
export interface WebSocketMessage {
  type: 'auction_update' | 'new_auction' | 'notification';
  data: any;
}

// Market stats types
export interface MarketStats {
  total_auctions: number;
  avg_ai_score: number;
  avg_price: number;
  by_city: {
    [city: string]: {
      count: number;
      avg_price: number;
      avg_score: number;
    };
  };
  by_property_type: {
    [type: string]: {
      count: number;
      avg_price: number;
      avg_score: number;
    };
  };
}

// Map marker type
export interface MapMarker {
  id: number;
  position: [number, number];
  title: string;
  price: number;
  score: number;
  property_type: PropertyType;
}
