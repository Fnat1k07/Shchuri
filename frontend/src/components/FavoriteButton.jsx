
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";
import "./FavoriteButton.css";

function FavoriteButton({ listing, onFavoriteChange }) {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [isFavorite, setIsFavorite] = useState(
    Boolean(listing.is_favorite)
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setIsFavorite(Boolean(listing.is_favorite));
  }, [listing.id, listing.is_favorite]);

  const handleClick = async (event) => {
    event.stopPropagation();

    if (!user) {
      navigate("/login");
      return;
    }

    if (loading) return;

    setLoading(true);

    try {
      if (isFavorite) {
        await api.delete(`favorites/${listing.id}/`);
        setIsFavorite(false);
        onFavoriteChange?.(false);
      } else {
        await api.post("favorites/", {
          listing_id: listing.id,
        });
        setIsFavorite(true);
        onFavoriteChange?.(true);
      }
    } catch (error) {
      console.error("Помилка роботи з обраним:", error);
      alert(
        error.response?.data?.detail ||
        "Не вдалося змінити список обраного. Спробуйте ще раз."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      className={`favorite-button ${isFavorite ? "favorite-active" : ""}`}
      onClick={handleClick}
      disabled={loading}
      aria-label={
        isFavorite ? "Видалити з обраного" : "Додати в обране"
      }
      title={
        isFavorite ? "Видалити з обраного" : "Додати в обране"
      }
    >
      {isFavorite ? "♥" : "♡"}
    </button>
  );
}

export default FavoriteButton;
