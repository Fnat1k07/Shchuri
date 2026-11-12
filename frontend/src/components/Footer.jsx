
import { Link } from "react-router-dom";
import "./Footer.css";

function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-container">
        <div className="footer-main">
          <div className="footer-brand">
            <Link to="/" className="footer-logo">
              HomeRent<span>.</span>
            </Link>

            <p>
              Платформа для пошуку та оренди житла.
              Знаходьте комфортне помешкання або здавайте
              власну нерухомість легко та зручно.
            </p>
          </div>

          <div className="footer-navigation">
            <h3>Навігація</h3>

            <div className="footer-links">
              <Link to="/">Головна</Link>
              <Link to="/login">Вхід</Link>
              <Link to="/register">Реєстрація</Link>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>© 2026 HomeRent. Усі права захищені.</p>
          <span>Створено для комфортної оренди житла</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
