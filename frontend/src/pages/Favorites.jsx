
import { useEffect, useState } from "react";
import api from "../api/axios";
import ListingCard from "../components/ListingCard";
import "./Favorites.css";

function Favorites() {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadFavorites = async () => {
      try {
        const response = await api.get("favorites/");

        const data = response.data;
        setFavorites(
          Array.isArray(data) ? data : data.results || []
        );
      } catch (err) {
        console.error("Помилка завантаження обраного:", err);
        setError("Не вдалося завантажити обрані оголошення.");
      } finally {
        setLoading(false);
      }
    };

    loadFavorites();
  }, []);

  const handleFavoriteChange = (listingId, isFavorite) => {
    if (!isFavorite) {
      setFavorites((current) =>
        current.filter(
          (favorite) => favorite.listing.id !== listingId
        )
      );
    }
  };

  if (loading) {
    return (
      <div className="favorites-message">
        Завантаження обраного...
      </div>
    );
  }

  if (error) {
    return (
      <div className="favorites-message">
        {error}
      </div>
    );
  }

  return (
    <div className="favorites-page">
      <div className="favorites-heading">
        <h1>Обране</h1>
        <p>Оголошення, які ти зберіг для перегляду</p>
      </div>

      {favorites.length === 0 ? (
        <div className="favorites-empty">
          <div className="favorites-empty-icon">♡</div>
          <h2>Поки що тут порожньо</h2>
          <p>
            Додавай цікаві оголошення в обране, натискаючи
            на сердечко.
          </p>
          <a href="/search" className="favorites-search-link">
            Знайти житло
          </a>
        </div>
      ) : (
        <>
          <p className="favorites-count">
            Збережено оголошень: {favorites.length}
          </p>

          <div className="favorites-grid">
            {favorites.map((favorite) => (
              <ListingCard
                key={favorite.id}
                listing={favorite.listing}
                onFavoriteChange={(isFavorite) =>
                  handleFavoriteChange(
                    favorite.listing.id,
                    isFavorite
                  )
                }
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default Favorites;
