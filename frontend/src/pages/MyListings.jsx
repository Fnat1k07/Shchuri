
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";
import { useNavigate } from "react-router-dom";

function MyListings() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchMyListings = async () => {
      try {
        const response = await api.get("listings/mine/");

        setListings(
          Array.isArray(response.data)
            ? response.data
            : response.data.results ?? []
        );
      } catch (err) {
        setError("Не вдалося завантажити ваші оголошення.");
      } finally {
        setLoading(false);
      }
    };

    if (user?.role === "owner") {
      fetchMyListings();
    } else {
      setLoading(false);
    }
  }, [user]);

  if (user?.role !== "owner") {
    return (
      <div className="my-listings-page">
        <h1>Мої оголошення</h1>
        <p>Ця сторінка доступна лише власникам житла.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="my-listings-page">Завантаження оголошень...</div>;
  }

  if (error) {
    return (
      <div className="my-listings-page">
        <h1>Мої оголошення</h1>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="my-listings-page">
      <div className="my-listings-header">
        <h1>Мої оголошення</h1>

        <button onClick={() => navigate("/listings/create")}>
          Додати оголошення
        </button>
      </div>

      {listings.length === 0 ? (
        <p>У вас поки немає оголошень.</p>
      ) : (
        <div className="my-listings-grid">
          {listings.map((listing) => {
            const coverImage = listing.images?.find(
              (image) => image.is_cover
            ) || listing.images?.[0];

            return (
              <div className="my-listing-card" key={listing.id}>
                <div className="my-listing-image">
                  {coverImage ? (
                    <img
                      src={coverImage.image}
                      alt={listing.title}
                    />
                  ) : (
                    <div className="no-listing-image">
                      Немає фотографії
                    </div>
                  )}
                </div>

                <div className="my-listing-content">
                  <h2>{listing.title}</h2>

                  <p className="my-listing-price">
                    {Number(listing.price).toLocaleString("uk-UA")} грн
                  </p>

                  <p>
                    {listing.city}, {listing.address}
                  </p>

                  <p>
                    {listing.rooms} кімн. · {listing.area} м²
                  </p>

                  <p className="my-listing-status">
                    Статус: {listing.status}
                  </p>

                  <button
                    onClick={() =>
                      navigate(`/listings/${listing.id}/edit`)
                    }
                  >
                    Редагувати
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default MyListings;
