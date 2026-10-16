import { createContext, useContext, useState } from "react";
import api from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const login = async (email, password) => {
    const response = await api.post("auth/login/", {
      email,
      password,
    });

    sessionStorage.setItem("access", response.data.access);
    sessionStorage.setItem("refresh", response.data.refresh);

    setUser(response.data.user);

    return response.data;
  };

  const logout = () => {
    sessionStorage.removeItem("access");
    sessionStorage.removeItem("refresh");

    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}