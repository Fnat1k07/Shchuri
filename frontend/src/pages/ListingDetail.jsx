
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";
import FavoriteButton from "../components/FavoriteButton";
import "./ListingDetail.css";

function ListingDetail() {
  const { id } = useParams();
  const { user } = useAuth();

  const [listing, setListing] = useState(null);
  const [amenities, setAmenities] = useState([]);
  const [selectedImage, setSelectedImage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadListing = async () => {
      try {
        setLoading(true);
        setError("");

        const [listingResponse, amenitiesResponse] =
          await Promise.all([
            api.get(`listings/${id}/`),
            api.get("amenities/"),
          ]);

        setListing(listingResponse.data);

        const amenitiesData = amenitiesResponse.data;
        setAmenities(
          Array.isArray(amenitiesData)
            ? amenitiesData
            : amenitiesData.results || []
        );
      } catch (err) {
        console.error("Помилка завантаження оголошення:", err);
        setError(
          err.response?.status === 404
            ? "Оголошення не знайдено або воно більше недоступне."
            : "Не вдалося завантажити оголошення. Спробуйте пізніше."
        );
      } finally {
        setLoading(false);
      }
    };

    loadListing();
  }, [id]);

  if (loading) {
    return (
      <div className="listing-detail-message">
        Завантаження оголошення...
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="listing-detail-message">
        <h2>{error || "Оголошення не знайдено"}</h2>
        <Link to="/search">Повернутися до пошуку</Link>
      </div>
    );
  }

  const images = listing.images || [];

  const propertyTypes = {
    apartment: "Квартира",
    house: "Будинок",
    room: "Кімната",
  };

  const listingAmenities = amenities.filter((amenity) =>
    listing.amenities?.includes(amenity.id)
  );

  const hasCoordinates =
    listing.latitude !== null &&
    listing.latitude !== undefined &&
    listing.longitude !== null &&
    listing.longitude !== undefined;

  const mapUrl = hasCoordinates
    ? `https://www.google.com/maps?q=${listing.latitude},${listing.longitude}`
    : null;

  const ownerName =
    listing.contact?.name?.trim() || "Власник житла";

  return (
    <div className="listing-detail-page">
      <Link to="/search" className="listing-detail-back">
        ← Повернутися до пошуку
      </Link>

      <div className="listing-detail-heading">
        <div>
          <h1>{listing.title}</h1>
          <p className="listing-detail-location">
            {listing.city}
            {listing.district ? `, ${listing.district}` : ""}
            {listing.address ? `, ${listing.address}` : ""}
          </p>
        </div>

        <FavoriteButton listing={listing} />
      </div>

      <section className="listing-detail-gallery">
        <div className="listing-detail-main-image">
          {images.length > 0 ? (
            <img
              src={images[selectedImage]?.image}
              alt={listing.title}
            />
          ) : (
            <div className="listing-detail-no-image">
              Фотографії відсутні
            </div>
          )}
        </div>

        {images.length > 1 && (
          <div className="listing-detail-thumbnails">
            {images.map((image, index) => (
              <button
                type="button"
                key={image.id}
                className={
                  selectedImage === index
                    ? "listing-detail-thumbnail active"
                    : "listing-detail-thumbnail"
                }
                onClick={() => setSelectedImage(index)}
              >
                <img
                  src={image.image}
                  alt={`Фотографія ${index + 1}`}
                />
              </button>
            ))}
          </div>
        )}
      </section>

      <div className="listing-detail-layout">
        <div className="listing-detail-main">
          <section className="listing-detail-section">
            <h2>Вартість оренди</h2>
            <p className="listing-detail-price">
              {Number(listing.price).toLocaleString("uk-UA")} грн
              <span> / місяць</span>
            </p>
          </section>

          <section className="listing-detail-section">
            <h2>Характеристики</h2>

            <div className="listing-detail-characteristics">
              <div>
                <span>Тип нерухомості</span>
                <strong>
                  {propertyTypes[listing.property_type] ||
                    listing.property_type}
                </strong>
              </div>

              <div>
                <span>Кількість кімнат</span>
                <strong>{listing.rooms}</strong>
              </div>

              <div>
                <span>Площа</span>
                <strong>{listing.area} м²</strong>
              </div>

              <div>
                <span>Місто</span>
                <strong>{listing.city}</strong>
              </div>

              {listing.district && (
                <div>
                  <span>Район</span>
                  <strong>{listing.district}</strong>
                </div>
              )}
            </div>
          </section>

          <section className="listing-detail-section">
            <h2>Опис</h2>
            <p className="listing-detail-description">
              {listing.description || "Опис відсутній."}
            </p>
          </section>

          <section className="listing-detail-section">
            <h2>Зручності</h2>

            {listingAmenities.length > 0 ? (
              <div className="listing-detail-amenities">
                {listingAmenities.map((amenity) => (
                  <span key={amenity.id}>
                    ✓ {amenity.name}
                  </span>
                ))}
              </div>
            ) : (
              <p>Інформація про зручності відсутня.</p>
            )}
          </section>

          <section className="listing-detail-section">
            <h2>Адреса та розташування</h2>

            <p className="listing-detail-address">
              {listing.city}
              {listing.district ? `, ${listing.district}` : ""}
              {listing.address ? `, ${listing.address}` : ""}
            </p>

            {mapUrl && (
              <a
                href={mapUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="listing-detail-map-link"
              >
                Переглянути на Google Maps
              </a>
            )}
          </section>
        </div>

        <aside className="listing-detail-sidebar">
          <div className="listing-detail-contact">
            <h2>Контакти власника</h2>

            <p className="listing-detail-owner">
              {ownerName}
            </p>

            {listing.contact?.phone ? (
              <a
                href={`tel:${listing.contact.phone}`}
                className="listing-detail-phone"
              >
                {listing.contact.phone}
              </a>
            ) : !user ? (
              <>
                <p className="listing-detail-phone-hint">
                  Увійдіть в обліковий запис, щоб переглянути номер телефону.
                </p>

                <Link
                  to="/login"
                  className="listing-detail-contact-button"
                >
                  Увійти в обліковий запис
                </Link>
              </>
            ) : (
              <p className="listing-detail-phone-hint">
                Номер телефону власника не вказаний.
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

export default ListingDetail;
