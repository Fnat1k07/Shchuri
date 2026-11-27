function ListingCard({ listing, onEdit, showStatus = false }) {
  const coverImage =
    listing.images?.find((image) => image.is_cover) ||
    listing.images?.[0];

  return (
    <article className="listing-card">
      <div className="listing-card-image">
        {coverImage ? (
          <img src={coverImage.image} alt={listing.title} />
        ) : (
          <div className="listing-card-no-image">
            Немає фотографії
          </div>
        )}
      </div>

      <div className="listing-card-content">
        <h2>{listing.title}</h2>

        <p className="listing-card-price">
          {Number(listing.price).toLocaleString("uk-UA")} грн
          <span> / місяць</span>
        </p>

        <p className="listing-card-location">
          {listing.city}
          {listing.district ? `, ${listing.district}` : ""}
        </p>

        <p className="listing-card-details">
          {listing.rooms} кімн. · {listing.area} м²
        </p>

        {listing.property_type && (
          <span className="listing-card-type">
            {{
              apartment: "Квартира",
              house: "Будинок",
              room: "Кімната",
            }[listing.property_type] || listing.property_type}
          </span>
        )}

        {showStatus && (
          <p className="listing-card-status">
            Статус: {listing.status}
          </p>
        )}

        {onEdit && (
          <button
            className="listing-card-edit-button"
            onClick={() => onEdit(listing.id)}
          >
            Редагувати
          </button>
        )}
      </div>
    </article>
  );
}

export default ListingCard;