
function ListingCard({ listing, onEdit }) {
  const coverImage = listing.images?.find(
    (image) => image.is_cover
  ) || listing.images?.[0];

  return (
    <div className="my-listing-card">
      <div className="my-listing-image">
        {coverImage ? (
          <img src={coverImage.image} alt={listing.title} />
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

       {onEdit && (
  <button onClick={() => onEdit(listing.id)}>
    Редагувати
  </button>
)}
      </div>
    </div>
  );
}

export default ListingCard;
