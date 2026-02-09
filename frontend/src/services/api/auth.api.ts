/**
 * Authentication API methods.
 * Phase 2 Week 1: refresh tokens, logout, OTP.
 */
import { apiClient } from './client';
import { User } from '../../types/user.types';

export interface RegisterRequest {
  email: string;
  password: string;
  timezone?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export const authApi = {
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', data);
    return response.data;
  },

  /** Log in as demo user (no credentials). POST /demo/login. Single mode: always available. */
  async demoLogin(): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/demo/login');
    return response.data;
  },

  /** Phase 3: Load sample workouts for demo user (authenticated). POST /demo/seed-me. */
  async demoSeedMe(): Promise<{ message: string; workouts_added: number }> {
    const response = await apiClient.post<{ message: string; workouts_added: number }>('/demo/seed-me');
    return response.data;
  },

  /** Exchange refresh token for new access + refresh tokens. POST /auth/refresh */
  async refresh(refreshToken: string): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /** Revoke current refresh token. POST /auth/logout */
  async logout(refreshToken: string): Promise<void> {
    await apiClient.post('/auth/logout', { refresh_token: refreshToken });
  },

  /** Revoke all refresh tokens for current user. POST /auth/logout-all */
  async logoutAll(): Promise<void> {
    await apiClient.post('/auth/logout-all');
  },

  /** Request OTP for email verification. POST /auth/request-otp */
  async requestOtp(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post<{ success: boolean; message: string }>('/auth/request-otp');
    return response.data;
  },

  /** Verify OTP. POST /auth/verify-otp */
  async verifyOtp(otp: string): Promise<{
    success: boolean;
    message: string;
    trial_started?: boolean;
    trial_ends_at?: string | null;
  }> {
    const response = await apiClient.post('/auth/verify-otp', { otp });
    return response.data;
  },
};
