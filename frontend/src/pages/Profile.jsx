
import { useEffect, useState } from "react";
import api from "../api/axios";
import "./Profile.css";

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
    return (
      <div className="profile-page">
        <div className="profile-message profile-error">
          <h2>Помилка</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="profile-page">
        <div className="profile-message">
          <div className="profile-loader"></div>
          <p>Завантаження профілю...</p>
        </div>
      </div>
    );
  }

  const fullName = `${user.first_name || ""} ${user.last_name || ""}`.trim();

  const roleName = user.role === "owner" ? "Власник" : "Орендар";

  const initials =
    `${user.first_name?.[0] || ""}${user.last_name?.[0] || ""}`.toUpperCase();

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="profile-heading">
          <span className="profile-label">HOMERENT ACCOUNT</span>
          <h1>Особистий кабінет</h1>
          <p>Переглядай інформацію про свій обліковий запис.</p>
        </div>

        <div className="profile-card">
          <div className="profile-card-header">
            <div className="profile-avatar">
              {initials || "U"}
            </div>

            <div className="profile-user-heading">
              <h2>{fullName || "Користувач HomeRent"}</h2>
              <span className="profile-role">{roleName}</span>
            </div>
          </div>

          <div className="profile-divider"></div>

          <div className="profile-information">
            <h3>Особиста інформація</h3>

            <div className="profile-info-row">
              <div className="profile-info-icon">@</div>
              <div className="profile-info-content">
                <span>Email</span>
                <p>{user.email || "Не вказано"}</p>
              </div>
            </div>

            <div className="profile-info-row">
              <div className="profile-info-icon">☎</div>
              <div className="profile-info-content">
                <span>Телефон</span>
                <p>{user.phone || "Не вказано"}</p>
              </div>
            </div>

            <div className="profile-info-row">
              <div className="profile-info-icon">♙</div>
              <div className="profile-info-content">
                <span>Ім'я та прізвище</span>
                <p>{fullName || "Не вказано"}</p>
              </div>
            </div>

            <div className="profile-info-row">
              <div className="profile-info-icon">⌂</div>
              <div className="profile-info-content">
                <span>Роль у системі</span>
                <p>{roleName}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="profile-note">
          <span>ℹ</span>
          <p>
            Це твій особистий кабінет HomeRent.
            Тут відображаються дані твого облікового запису.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Profile;
