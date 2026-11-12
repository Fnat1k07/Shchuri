
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Header.css";

function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

 const handleLogout = () => {
  logout();
  navigate("/");
};

  return (
    <header className="site-header">
      <div className="header-container">
        <NavLink to="/" className="logo">
          HomeRent
        </NavLink>

        <nav className="header-nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Головна
          </NavLink>

          {user ? (
            <>
              <NavLink
                to="/profile"
                className={({ isActive }) =>
                  isActive ? "nav-link active" : "nav-link"
                }
              >
                Кабінет
              </NavLink>

              <button
                type="button"
                className="header-button"
                onClick={handleLogout}
              >
                Вийти
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className={({ isActive }) =>
                  isActive ? "nav-link active" : "nav-link"
                }
              >
                Вхід
              </NavLink>

              <NavLink to="/register" className="register-link">
                Реєстрація
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;
