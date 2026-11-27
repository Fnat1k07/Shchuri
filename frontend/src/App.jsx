
import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import Home from "./pages/Home";
import Search from "./pages/Search";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import MyListings from "./pages/MyListings";

import "./App.css";

import Header from "./components/Header";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";
import ListingForm from "./components/ListingForm";

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Header />

        <main className="page-content">
          <Routes>
            <Route path="/" element={<Home />} />

            <Route path="/search" element={<Search />} />

            <Route path="/login" element={<Login />} />

            <Route path="/register" element={<Register />} />

            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />

            <Route
              path="/my-listings"
              element={
                <ProtectedRoute>
                  <MyListings />
                </ProtectedRoute>
              }
            />

            <Route
              path="/listings/create"
              element={
                <ProtectedRoute>
                  <ListingForm />
                </ProtectedRoute>
              }
            />

            <Route
              path="/listings/:id/edit"
              element={
                <ProtectedRoute>
                  <ListingForm />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>

        <Footer />
      </div>
    </BrowserRouter>
  );
}

export default App;
