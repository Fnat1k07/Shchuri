
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Login.css";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    try {
      await login(email, password);
      navigate("/profile");
    } catch (err) {
      setError("Помилка входу. Перевірте email та пароль.");
      console.error(err);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-icon">⌂</div>

        <div className="login-heading">
          <h1>Вхід у HomeRent</h1>
          <p>
            Увійдіть до свого облікового запису,
            щоб продовжити.
          </p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-form-group">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              placeholder="example@gmail.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <div className="login-form-group">
            <label htmlFor="login-password">Пароль</label>
            <input
              id="login-password"
              type="password"
              placeholder="Введіть пароль"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          <button className="login-submit-button" type="submit">
            Увійти
          </button>
        </form>

        <div className="login-register-link">
          Ще не маєте акаунта?
          <Link to="/register"> Зареєструватися</Link>
        </div>
      </div>
    </div>
  );
}

export default Login;
