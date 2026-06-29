import { create } from "zustand";

import {
  api,
  setAccessToken,
} from "@/lib/api";

import type {
  LoginRequest,
  RegisterRequest,
  User,
} from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (
    body: LoginRequest
  ) => Promise<void>;

  register: (
    body: RegisterRequest
  ) => Promise<void>;

  logout: () => Promise<void>;

  loadUser: () => Promise<void>;
}

export const useAuthStore =
  create<AuthState>((set) => ({

    user: null,
    isAuthenticated: false,
    isLoading: false,


    login: async (body) => {

      set({ isLoading: true });

      try {

        const tokens =
          await api.auth.login(body);

        setAccessToken(
          tokens.access_token
        );

        const user =
          await api.auth.me();

        set({
          user,
          isAuthenticated: true,
        });

      } finally {

        set({ isLoading: false });

      }
    },


    register: async (body) => {

      set({ isLoading: true });

      try {

        await api.auth.register(body);

        const tokens =
          await api.auth.login({
            email: body.email,
            password: body.password
          });

        setAccessToken(
          tokens.access_token
        );

        const user =
          await api.auth.me();

        set({
          user,
          isAuthenticated: true,
        });

      } finally {

        set({ isLoading: false });

      }
    },


    logout: async () => {

      try {

        await api.auth.logout();

      } catch {}

      setAccessToken(null);

      set({
        user: null,
        isAuthenticated: false,
      });
    },


    loadUser: async () => {

      try {

        const refresh =
          await api.auth.refresh();

        setAccessToken(
          refresh.access_token
        );

        const user =
          await api.auth.me();

        set({
          user,
          isAuthenticated: true,
        });

      } catch {

        setAccessToken(null);

        set({
          user: null,
          isAuthenticated: false,
        });
      }
    },
  }));