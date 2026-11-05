
import { useEffect, useState } from "react";
import api from "../api/axios";

function Profile() {
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const getProfile = async () => {
      try {
        const token = sessionStorage.getItem("access");

        const response = await api.get("users/me/", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        setUser(response.data);
      } catch (err) {
        setError("Не вдалося завантажити профіль");
      }
    };

    getProfile();
  }, []);

  if (error) {
    return <p>{error}</p>;
  }

  if (!user) {
    return <p>Завантаження профілю...</p>;
  }

  return (
    <div>
      <h1>Особистий кабінет</h1>

      <p>Ім'я: {user.first_name}</p>
      <p>Прізвище: {user.last_name}</p>
      <p>Email: {user.email}</p>
      <p>Телефон: {user.phone}</p>
      <p>
        Роль: {user.role === "owner" ? "Власник" : "Орендар"}
      </p>
    </div>
  );
}

export default Profile;
