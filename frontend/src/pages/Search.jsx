
import { useEffect, useState } from "react";

import api from "../api/axios";
import ListingCard from "../components/ListingCard";

import "./Home.css";
import "./Search.css";

function Search() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [filters, setFilters] = useState({
    search: "",
    city: "",
    district: "",
    property_type: "",
    price_min: "",
    price_max: "",
    area_min: "",
    area_max: "",
    rooms: "",
  });

  const [appliedFilters, setAppliedFilters] = useState({});
  const [ordering, setOrdering] = useState("-created_at");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const pageSize = 12;
  const totalPages = Math.ceil(totalCount / pageSize);

  // Завантаження оголошень з урахуванням фільтрів і сортування
  useEffect(() => {
    const fetchListings = async () => {
      setLoading(true);
      setError("");

      try {
        const params = {
          page,
          page_size: pageSize,
          ordering,
          ...appliedFilters,
        };

        const response = await api.get("listings/", { params });

        setListings(response.data.results ?? []);
        setTotalCount(response.data.count ?? 0);
      } catch (err) {
        console.error("Помилка завантаження оголошень:", err);

        setError(
          "Не вдалося завантажити оголошення. Спробуйте оновити сторінку."
        );

        setListings([]);
        setTotalCount(0);
      } finally {
        setLoading(false);
      }
    };

    fetchListings();
  }, [appliedFilters, ordering, page]);

  // Зміна значень полів фільтра
  const handleFilterChange = (event) => {
    const { name, value } = event.target;

    setFilters((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // Застосування фільтрів
  const handleSearch = (event) => {
    event.preventDefault();

    const preparedFilters = {};

    Object.entries(filters).forEach(([key, value]) => {
      if (value.trim() !== "") {
        preparedFilters[key] = value.trim();
      }
    });

    setPage(1);
    setAppliedFilters(preparedFilters);
  };

  // Скидання фільтрів
  const handleReset = () => {
    setFilters({
      search: "",
      city: "",
      district: "",
      property_type: "",
      price_min: "",
      price_max: "",
      area_min: "",
      area_max: "",
      rooms: "",
    });

    setAppliedFilters({});
    setPage(1);
    setOrdering("-created_at");
  };

  return (
    <div className="search-page">
      <section className="home-catalog">
        <div className="home-section-heading">
          <span>КАТАЛОГ HOMERENT</span>
          <h2>Знайди своє ідеальне житло</h2>
          <p>
            Використовуй фільтри, щоб знайти житло,
            яке відповідає твоїм потребам.
          </p>
        </div>

        <form className="catalog-filters" onSubmit={handleSearch}>
          <div className="catalog-search">
            <input
              type="text"
              name="search"
              value={filters.search}
              onChange={handleFilterChange}
              placeholder="Пошук за назвою, описом або адресою..."
            />

            <button type="submit">Знайти</button>
          </div>

          <div className="catalog-filter-grid">
            <div className="catalog-filter-field">
              <label htmlFor="search-city">Місто</label>
              <input
                id="search-city"
                type="text"
                name="city"
                value={filters.city}
                onChange={handleFilterChange}
                placeholder="Наприклад, Львів"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="search-district">Район</label>
              <input
                id="search-district"
                type="text"
                name="district"
                value={filters.district}
                onChange={handleFilterChange}
                placeholder="Назва району"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="search-property-type">Тип житла</label>
              <select
                id="search-property-type"
                name="property_type"
                value={filters.property_type}
                onChange={handleFilterChange}
              >
                <option value="">Усі типи</option>
                <option value="apartment">Квартира</option>
                <option value="house">Будинок</option>
                <option value="room">Кімната</option>
              </select>
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="search-rooms">Кількість кімнат</label>
              <input
                id="search-rooms"
                type="number"
                name="rooms"
                min="1"
                value={filters.rooms}
                onChange={handleFilterChange}
                placeholder="Наприклад, 2"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="search-price-min">Ціна від (грн)</label>
              <input
                id="search-price-min"
                type="number"
                name="price_min"
                min="0"
                value={filters.price_min}
                onChange={handleFilterChange}
                placeholder="Мінімальна ціна"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="search-price-max">Ціна до (грн)</label>
              <input
                id="search-price-max"
                type="number"
                name="price_max"
                min="0"
                value={filters.price_max}
                onChange={handleFilterChange}
                placeholder="Максимальна ціна"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="search-area-min">Площа від (м²)</label>
              <input
                id="search-area-min"
                type="number"
                name="area_min"
                min="0"
                step="0.1"
                value={filters.area_min}
                onChange={handleFilterChange}
                placeholder="Мінімальна площа"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="search-area-max">Площа до (м²)</label>
              <input
                id="search-area-max"
                type="number"
                name="area_max"
                min="0"
                step="0.1"
                value={filters.area_max}
                onChange={handleFilterChange}
                placeholder="Максимальна площа"
              />
            </div>
          </div>

          <div className="catalog-filter-actions">
            <button type="submit" className="catalog-apply-button">
              Застосувати фільтри
            </button>

            <button
              type="button"
              className="catalog-reset-button"
              onClick={handleReset}
            >
              Скинути фільтри
            </button>
          </div>
        </form>

        <div className="catalog-toolbar">
          <p>
            Знайдено оголошень: <strong>{totalCount}</strong>
          </p>

          <div className="catalog-sort">
            <label htmlFor="search-ordering">Сортування:</label>

            <select
              id="search-ordering"
              value={ordering}
              onChange={(event) => {
                setOrdering(event.target.value);
                setPage(1);
              }}
            >
              <option value="-created_at">Спочатку новіші</option>
              <option value="created_at">Спочатку старіші</option>
              <option value="price">Спочатку дешевші</option>
              <option value="-price">Спочатку дорожчі</option>
              <option value="-area">За найбільшою площею</option>
              <option value="area">За найменшою площею</option>
              <option value="-rooms">За кількістю кімнат</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="catalog-message">
            Завантаження оголошень...
          </div>
        ) : error ? (
          <div className="catalog-message catalog-error">
            {error}
          </div>
        ) : listings.length === 0 ? (
          <div className="catalog-message">
            <h3>Оголошень не знайдено</h3>
            <p>
              Спробуйте змінити параметри пошуку або скинути фільтри.
            </p>
          </div>
        ) : (
          <div className="catalog-listings-grid">
            {listings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}

        {!loading && !error && totalPages > 1 && (
          <div className="catalog-pagination">
            <button
              type="button"
              disabled={page === 1}
              onClick={() => setPage((previous) => previous - 1)}
            >
              Попередня
            </button>

            <span>
              Сторінка {page} з {totalPages}
            </span>

            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((previous) => previous + 1)}
            >
              Наступна
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

export default Search;
