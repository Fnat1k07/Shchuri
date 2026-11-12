
import "./Home.css";

function Home() {
  return (
    <div className="home-page">
      <section className="home-hero">
        <div className="home-hero-content">
          <span className="home-label">HomeRent — твій новий дім</span>

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
              onClick={() => {
                alert("Сторінка пошуку житла буде доступна пізніше.");
              }}
            >
              Знайти житло
            </button>

            <button
              className="home-secondary-button"
              onClick={() => {
                alert("Створення оголошень буде доступне пізніше.");
              }}
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
