
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../api/axios";
import ListingCard from "../components/ListingCard";

import "./Home.css";

function Home() {
  const navigate = useNavigate();

  // Оголошення з сервера
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Дані форми пошуку
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

  // Застосовані фільтри
  const [appliedFilters, setAppliedFilters] = useState({});

  // Сортування та сторінка
  const [ordering, setOrdering] = useState("-created_at");
  const [page, setPage] = useState(1);

  // Інформація про пагінацію
  const [totalCount, setTotalCount] = useState(0);

  const pageSize = 12;
  const totalPages = Math.ceil(totalCount / pageSize);

  // Отримання оголошень з API
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

        // Django REST Framework повертає результати в results
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

  // Застосування пошуку та фільтрів
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
    const emptyFilters = {
      search: "",
      city: "",
      district: "",
      property_type: "",
      price_min: "",
      price_max: "",
      area_min: "",
      area_max: "",
      rooms: "",
    };

    setFilters(emptyFilters);
    setAppliedFilters({});
    setPage(1);
    setOrdering("-created_at");
  };

  // Перехід до каталогу
  const scrollToCatalog = () => {
    document.getElementById("catalog")?.scrollIntoView({
      behavior: "smooth",
    });
  };

  return (
    <div className="home-page">
      {/* Головний банер */}
      <section className="home-hero">
        <div className="home-hero-content">
          <span className="home-label">
            HomeRent — твій новий дім
          </span>

          <h1>
            Знайди житло,
            <br />
            <span>у якому захочеться жити</span>
          </h1>

          <p>
            Зручний пошук квартир для оренди.
            Обирай район, бюджет та характеристики,
            щоб знайти ідеальне житло.
          </p>

          <div className="home-actions">
            <button
              className="home-primary-button"
              onClick={scrollToCatalog}
            >
              Знайти житло
            </button>

            <button
              className="home-secondary-button"
              onClick={() => navigate("/listings/create")}
            >
              Здати житло
            </button>
          </div>
        </div>

        <div className="home-hero-image">
          <div className="home-image-overlay">
            <span>Твій комфорт починається тут</span>
          </div>
        </div>
      </section>

      {/* Каталог оголошень */}
      <section className="home-catalog" id="catalog">
        <div className="home-section-heading">
          <span>КАТАЛОГ HOMERENT</span>
          <h2>Знайди своє ідеальне житло</h2>
          <p>
            Переглядай актуальні оголошення та обирай
            житло відповідно до своїх потреб.
          </p>
        </div>

        {/* Форма пошуку та фільтрів */}
        <form className="catalog-filters" onSubmit={handleSearch}>
          <div className="catalog-search">
            <input
              type="text"
              name="search"
              value={filters.search}
              onChange={handleFilterChange}
              placeholder="Пошук за назвою, описом або адресою..."
            />

            <button type="submit">
              Знайти
            </button>
          </div>

          <div className="catalog-filter-grid">
            <div className="catalog-filter-field">
              <label htmlFor="city">Місто</label>
              <input
                id="city"
                type="text"
                name="city"
                value={filters.city}
                onChange={handleFilterChange}
                placeholder="Наприклад, Львів"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="district">Район</label>
              <input
                id="district"
                type="text"
                name="district"
                value={filters.district}
                onChange={handleFilterChange}
                placeholder="Назва району"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="property_type">Тип житла</label>
              <select
                id="property_type"
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
              <label htmlFor="rooms">Кількість кімнат</label>
              <input
                id="rooms"
                type="number"
                name="rooms"
                min="1"
                value={filters.rooms}
                onChange={handleFilterChange}
                placeholder="Наприклад, 2"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="price_min">Ціна від (грн)</label>
              <input
                id="price_min"
                type="number"
                name="price_min"
                min="0"
                value={filters.price_min}
                onChange={handleFilterChange}
                placeholder="Мінімальна ціна"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="price_max">Ціна до (грн)</label>
              <input
                id="price_max"
                type="number"
                name="price_max"
                min="0"
                value={filters.price_max}
                onChange={handleFilterChange}
                placeholder="Максимальна ціна"
              />
            </div>

            <div className="catalog-filter-field">
              <label htmlFor="area_min">Площа від (м²)</label>
              <input
                id="area_min"
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
              <label htmlFor="area_max">Площа до (м²)</label>
              <input
                id="area_max"
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

        {/* Сортування та кількість оголошень */}
        <div className="catalog-toolbar">
          <p>
            Знайдено оголошень: <strong>{totalCount}</strong>
          </p>

          <div className="catalog-sort">
            <label htmlFor="ordering">Сортування:</label>

            <select
              id="ordering"
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

        {/* Результати пошуку */}
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
              <ListingCard
                key={listing.id}
                listing={listing}
              />
            ))}
          </div>
        )}

        {/* Пагінація */}
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

      {/* Переваги HomeRent */}
      <section className="home-benefits">
        <div className="home-section-heading">
          <span>ПЕРЕВАГИ HOMERENT</span>
          <h2>Оренда житла без зайвих турбот</h2>
        </div>

        <div className="home-benefits-grid">
          <div className="home-benefit-card">
            <div className="home-benefit-icon">⌕</div>
            <h3>Зручний пошук</h3>
            <p>
              Знаходь житло за ціною, містом та
              потрібними характеристиками.
            </p>
          </div>

          <div className="home-benefit-card">
            <div className="home-benefit-icon">⌂</div>
            <h3>Різноманіття житла</h3>
            <p>
              Обирай квартиру, яка відповідає
              твоїм потребам.
            </p>
          </div>

          <div className="home-benefit-card">
            <div className="home-benefit-icon">♡</div>
            <h3>Обране</h3>
            <p>
              Зберігай цікаві оголошення,
              щоб повернутися до них пізніше.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
