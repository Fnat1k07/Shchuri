
import {
  createContext,
  useContext,
  useState,
  useEffect,
} from "react";

import api from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Відновлення авторизації після перезавантаження
  useEffect(() => {
    const restoreAuth = async () => {
      const token = sessionStorage.getItem("access");

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await api.get("users/me/", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        setUser(response.data);
      } catch (error) {
        sessionStorage.removeItem("access");
        sessionStorage.removeItem("refresh");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    restoreAuth();
  }, []);

  // Вхід
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

  // Вихід
  const logout = () => {
    sessionStorage.removeItem("access");
    sessionStorage.removeItem("refresh");

    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, login, logout, loading }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
