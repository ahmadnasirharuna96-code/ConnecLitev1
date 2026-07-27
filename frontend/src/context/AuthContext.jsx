import { createContext, useContext, useEffect, useState } from "react";
import apiClient from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("connectlite_access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    apiClient
      .get("/auth/me/")
      .then(({ data }) => setUser(data))
      .catch(() => {
        localStorage.removeItem("connectlite_access_token");
        localStorage.removeItem("connectlite_refresh_token");
      })
      .finally(() => setIsLoading(false));
  }, []);

  function storeTokens(tokens) {
    localStorage.setItem("connectlite_access_token", tokens.access);
    localStorage.setItem("connectlite_refresh_token", tokens.refresh);
  }

  async function register(payload) {
    const { data } = await apiClient.post("/auth/register/", payload);
    return data;
  }

  async function requestOtp(phone_number, purpose = "registration") {
    const { data } = await apiClient.post("/auth/request-otp/", { phone_number, purpose });
    return data;
  }

  async function verifyOtp(phone_number, code, purpose = "registration") {
    const { data } = await apiClient.post("/auth/verify-otp/", { phone_number, code, purpose });
    storeTokens(data.tokens);
    setUser(data.user);
    return data;
  }

  async function login(phone_number, password) {
    const { data } = await apiClient.post("/auth/login/", { phone_number, password });
    storeTokens(data.tokens);
    setUser(data.user);
    return data;
  }

  async function logout() {
    const refresh = localStorage.getItem("connectlite_refresh_token");
    try {
      if (refresh) await apiClient.post("/auth/logout/", { refresh });
    } finally {
      localStorage.removeItem("connectlite_access_token");
      localStorage.removeItem("connectlite_refresh_token");
      setUser(null);
    }
  }

  const value = { user, isLoading, register, requestOtp, verifyOtp, login, logout };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
