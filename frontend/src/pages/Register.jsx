
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/axios";
import "./Register.css";

function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    role: "tenant",
    password: "",
    password2: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm({
      ...form,
      [name]: value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (form.password !== form.password2) {
      setError("Паролі не збігаються");
      return;
    }

    setLoading(true);

    try {
      await api.post("auth/register/", form);
      alert("Реєстрація успішна!");
      navigate("/login");
    } catch (err) {
      const data = err.response?.data;

      if (data && typeof data === "object") {
        const messages = Object.values(data).flat().join(" ");
        setError(messages || "Помилка реєстрації");
      } else {
        setError("Не вдалося з'єднатися із сервером");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="register-page">
      <div className="register-card">
        <div className="register-heading">
          <span className="register-label">HOMERENT</span>
          <h1>Створити акаунт</h1>
          <p>
            Приєднуйтесь до HomeRent та знаходьте житло
            або здавайте власну нерухомість.
          </p>
        </div>

        <form className="register-form" onSubmit={handleSubmit}>
          <div className="register-fields">
            <div className="register-field">
              <label htmlFor="first_name">Ім'я</label>
              <input
                id="first_name"
                type="text"
                name="first_name"
                placeholder="Ваше ім'я"
                value={form.first_name}
                onChange={handleChange}
                autoComplete="given-name"
                required
              />
            </div>

            <div className="register-field">
              <label htmlFor="last_name">Прізвище</label>
              <input
                id="last_name"
                type="text"
                name="last_name"
                placeholder="Ваше прізвище"
                value={form.last_name}
                onChange={handleChange}
                autoComplete="family-name"
                required
              />
            </div>

            <div className="register-field register-field-full">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                name="email"
                placeholder="example@email.com"
                value={form.email}
                onChange={handleChange}
                autoComplete="email"
                required
              />
            </div>

            <div className="register-field register-field-full">
              <label htmlFor="phone">Номер телефону</label>
              <input
                id="phone"
                type="tel"
                name="phone"
                placeholder="+380..."
                value={form.phone}
                onChange={handleChange}
                autoComplete="tel"
              />
            </div>

            <div className="register-field register-field-full">
              <label htmlFor="role">Тип облікового запису</label>
              <select
                id="role"
                name="role"
                value={form.role}
                onChange={handleChange}
              >
                <option value="tenant">Орендар</option>
                <option value="owner">Власник житла</option>
              </select>
            </div>

            <div className="register-field">
              <label htmlFor="password">Пароль</label>
              <input
                id="password"
                type="password"
                name="password"
                placeholder="Створіть пароль"
                value={form.password}
                onChange={handleChange}
                autoComplete="new-password"
                required
              />
            </div>

            <div className="register-field">
              <label htmlFor="password2">Підтвердження пароля</label>
              <input
                id="password2"
                type="password"
                name="password2"
                placeholder="Повторіть пароль"
                value={form.password2}
                onChange={handleChange}
                autoComplete="new-password"
                required
              />
            </div>
          </div>

          {error && (
            <div className="register-error">
              {error}
            </div>
          )}

          <button
            className="register-button"
            type="submit"
            disabled={loading}
          >
            {loading ? "Створення акаунта..." : "Зареєструватися"}
          </button>
        </form>

        <div className="register-footer">
          <span>Уже маєте акаунт?</span>
          <Link to="/login">Увійти</Link>
        </div>
      </div>
    </main>
  );
}

export default Register;
