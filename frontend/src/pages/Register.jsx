
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/axios";

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
    <div>
      <h1>Реєстрація в HomeRent</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label>Ім'я:</label>
          <input
            type="text"
            name="first_name"
            value={form.first_name}
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label>Прізвище:</label>
          <input
            type="text"
            name="last_name"
            value={form.last_name}
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label>Телефон:</label>
          <input
            type="tel"
            name="phone"
            value={form.phone}
            onChange={handleChange}
          />
        </div>

        <div>
          <label>Роль:</label>
          <select
            name="role"
            value={form.role}
            onChange={handleChange}
          >
            <option value="tenant">Орендар</option>
            <option value="owner">Власник житла</option>
          </select>
        </div>

        <div>
          <label>Пароль:</label>
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label>Підтвердження пароля:</label>
          <input
            type="password"
            name="password2"
            value={form.password2}
            onChange={handleChange}
            required
          />
        </div>

        {error && <p style={{ color: "red" }}>{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Реєстрація..." : "Зареєструватися"}
        </button>
      </form>

      <p>
        Уже маєте акаунт? <Link to="/login">Увійти</Link>
      </p>
    </div>
  );
}

export default Register;
