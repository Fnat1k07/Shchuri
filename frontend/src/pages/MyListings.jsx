
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";
import { useNavigate } from "react-router-dom";
import ListingCard from "../components/ListingCard";

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
    return (
      <div className="my-listings-page">
        Завантаження оголошень...
      </div>
    );
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
          {listings.map((listing) => (
            <ListingCard
              key={listing.id}
              listing={listing}
              onEdit={(id) => navigate(`/listings/${id}/edit`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default MyListings;
