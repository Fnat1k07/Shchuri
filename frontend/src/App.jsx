import {
  BrowserRouter,
  Routes,
  Route,
  Link
} from "react-router-dom";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";

import ProtectedRoute from "./components/ProtectedRoute"

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Головна</Link> |{" "}
        <Link to="/login">Вхід</Link> |{" "}
        <Link to="/register">Реєстрація</Link> |{" "}
        <Link to="/profile">Кабінет</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/profile" element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
          } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;