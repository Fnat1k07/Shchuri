
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import api from "../api/axios";

import "./ListingForm.css";

function ListingForm() {
  const { id } = useParams();
  const navigate = useNavigate();

  const isEditing = Boolean(id);

  const [amenities, setAmenities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  
  const [existingImages, setExistingImages] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [coverSelection, setCoverSelection] = useState(null);
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    price: "",
    property_type: "apartment",
    rooms: "",
    area: "",
    city: "",
    district: "",
    address: "",
    latitude: "",
    longitude: "",
    amenities: [],
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        const amenitiesResponse = await api.get("amenities/");
        setAmenities(amenitiesResponse.data.results ?? amenitiesResponse.data);

       if (isEditing) {
  const response = await api.get(`listings/${id}/`);
  const listing = response.data;
setExistingImages(listing.images ?? []);

          setFormData({
            title: listing.title ?? "",
            description: listing.description ?? "",
            price: listing.price ?? "",
            property_type: listing.property_type ?? "apartment",
            rooms: listing.rooms ?? "",
            area: listing.area ?? "",
            city: listing.city ?? "",
            district: listing.district ?? "",
            address: listing.address ?? "",
            latitude: listing.latitude ?? "",
            longitude: listing.longitude ?? "",
            amenities: listing.amenities ?? [],
          });
        }
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          "Не вдалося завантажити дані форми."
        );
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id, isEditing]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleAmenityChange = (amenityId) => {
    setFormData((previous) => ({
      ...previous,
      amenities: previous.amenities.includes(amenityId)
        ? previous.amenities.filter((item) => item !== amenityId)
        : [...previous.amenities, amenityId],
    }));
  };

  const handleFileChange = (event) => {
  const files = Array.from(event.target.files);

  const totalImages = existingImages.length + selectedFiles.length;

  if (totalImages + files.length > 8) {
    setError("Можна додати максимум 8 фотографій.");
    event.target.value = "";
    return;
  }

  const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
  const maxSize = 5 * 1024 * 1024;

  const validFiles = files.filter((file) => {
    if (!allowedTypes.includes(file.type)) {
      setError("Дозволені лише JPEG, PNG та WEBP.");
      return false;
    }

    if (file.size > maxSize) {
      setError("Розмір фотографії не повинен перевищувати 5 МБ.");
      return false;
    }

    return true;
  });

  const newFiles = validFiles.map((file) => ({
    file,
    preview: URL.createObjectURL(file),
    key: `new-${crypto.randomUUID()}`,
  }));

  setSelectedFiles((previous) => [...previous, ...newFiles]);

  if (!coverSelection && newFiles.length > 0) {
    setCoverSelection(newFiles[0].key);
  }

  event.target.value = "";
};

const removeSelectedFile = (key) => {
  setSelectedFiles((previous) => {
    const file = previous.find((item) => item.key === key);

    if (file) {
      URL.revokeObjectURL(file.preview);
    }

    const updated = previous.filter((item) => item.key !== key);

    if (coverSelection === key) {
      setCoverSelection(
        updated[0]?.key ??
        (existingImages[0] ? `existing-${existingImages[0].id}` : null)
      );
    }

    return updated;
  });
};

const deleteExistingImage = async (imageId) => {
  try {
    await api.delete(`listings/${id}/images/${imageId}/`);

    const updated = existingImages.filter((image) => image.id !== imageId);
    setExistingImages(updated);

    if (coverSelection === `existing-${imageId}`) {
      setCoverSelection(
        updated[0] ? `existing-${updated[0].id}` : selectedFiles[0]?.key ?? null
      );
    }
  } catch (err) {
    setError("Не вдалося видалити фотографію.");
  }
};

const handleCoverChange = async (selection) => {
  setCoverSelection(selection);

  if (!selection.startsWith("existing-")) {
    return;
  }

  const imageId = selection.replace("existing-", "");

  try {
    await api.post(`listings/${id}/images/${imageId}/cover/`);

    setExistingImages((previous) =>
      previous.map((image) => ({
        ...image,
        is_cover: image.id === Number(imageId),
      }))
    );
  } catch (err) {
    setError("Не вдалося змінити обкладинку.");
  }
};

  
const handleSubmit = async (event) => {
  event.preventDefault();
  setError("");

  try {
    setSaving(true);

    const data = {
      ...formData,
      price: Number(formData.price),
      rooms: Number(formData.rooms),
      area: Number(formData.area),
      latitude: formData.latitude === "" ? null : Number(formData.latitude),
      longitude: formData.longitude === "" ? null : Number(formData.longitude),
    };

    let listingId = id;

    // Створення або оновлення оголошення
    if (isEditing) {
      await api.patch(`listings/${id}/`, data);
    } else {
      const response = await api.post("listings/", data);
      listingId = response.data.id;
    }

    // Завантаження нових фотографій
    const uploadedImages = [];

    for (const item of selectedFiles) {
      const imageData = new FormData();
      imageData.append("image", item.file);

      const response = await api.post(
        `listings/${listingId}/images/`,
        imageData
      );

      uploadedImages.push({
        key: item.key,
        id: response.data.id,
      });
    }

    // Якщо користувач вибрав нову фотографію обкладинкою
    if (coverSelection?.startsWith("new-")) {
      const coverImage = uploadedImages.find(
        (image) => image.key === coverSelection
      );

      if (coverImage) {
        await api.post(
          `listings/${listingId}/images/${coverImage.id}/cover/`
        );
      }
    }

    // Очищення тимчасових URL фотографій
    selectedFiles.forEach((item) => {
      URL.revokeObjectURL(item.preview);
    });

    navigate("/profile");
  } catch (err) {
    const responseData = err.response?.data;

    if (responseData && typeof responseData === "object") {
      const messages = Object.entries(responseData).map(
        ([field, messages]) => {
          const text = Array.isArray(messages)
            ? messages.join(" ")
            : String(messages);

          return `${field}: ${text}`;
        }
      );

      setError(messages.join("\n"));
    } else {
      setError("Не вдалося зберегти оголошення.");
    }
  } finally {
    setSaving(false);
  }
};

  if (loading) {
    return <p>Завантаження форми...</p>;
  }

  return (
    <section className="listing-form">
      <h1>
        {isEditing ? "Редагування оголошення" : "Створення оголошення"}
      </h1>

      {error && <p className="form-error">{error}</p>}

      <form onSubmit={handleSubmit}>
        <label>
          Назва оголошення
          <input
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            minLength={5}
          />
        </label>

        <label>
          Опис
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={5}
          />
        </label>

        <label>
          Тип нерухомості
          <select
            name="property_type"
            value={formData.property_type}
            onChange={handleChange}
          >
            <option value="apartment">Квартира</option>
            <option value="house">Будинок</option>
            <option value="room">Кімната</option>
          </select>
        </label>

        <label>
          Ціна за місяць
          <input
            type="number"
            name="price"
            value={formData.price}
            onChange={handleChange}
            min="0.01"
            max="1000000"
            step="0.01"
            required
          />
        </label>

        <label>
          Кількість кімнат
          <input
            type="number"
            name="rooms"
            value={formData.rooms}
            onChange={handleChange}
            min="1"
            max="20"
            required
          />
        </label>

        <label>
          Площа (м²)
          <input
            type="number"
            name="area"
            value={formData.area}
            onChange={handleChange}
            min="1"
            max="10000"
            step="0.1"
            required
          />
        </label>

        <label>
          Місто
          <input
            name="city"
            value={formData.city}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Район
          <input
            name="district"
            value={formData.district}
            onChange={handleChange}
          />
        </label>

        <label>
          Адреса
          <input
            name="address"
            value={formData.address}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Широта
          <input
            type="number"
            name="latitude"
            value={formData.latitude}
            onChange={handleChange}
            min="-90"
            max="90"
            step="any"
          />
        </label>

        <label>
          Довгота
          <input
            type="number"
            name="longitude"
            value={formData.longitude}
            onChange={handleChange}
            min="-180"
            max="180"
            step="any"
          />
        </label>

        <fieldset>
          <legend>Зручності</legend>

          {amenities.map((amenity) => (
            <label key={amenity.id}>
              <input
                type="checkbox"
                checked={formData.amenities.includes(amenity.id)}
                onChange={() => handleAmenityChange(amenity.id)}
              />
              {amenity.name}
            </label>
          ))}
        </fieldset>


<div className="photo-section">
  <h2>Фотографії</h2>

  <p>
    Додано: {existingImages.length + selectedFiles.length} / 8
  </p>

  <label className="photo-upload">
    Додати фотографії
    <input
      type="file"
      accept="image/jpeg,image/png,image/webp"
      multiple
      onChange={handleFileChange}
      disabled={existingImages.length + selectedFiles.length >= 8}
    />
  </label>

  <div className="photo-grid">
    {existingImages.map((image) => (
  <div className="photo-card" key={`existing-${image.id}`}>
    <img
      src={image.image}
      alt="Фотографія оголошення"
    />

    <p>ID фотографії: {image.id}</p>

    <div className="photo-actions">
      <label>
        <input
          type="radio"
          name="cover"
          checked={coverSelection === `existing-${image.id}`}
          onChange={() => handleCoverChange(`existing-${image.id}`)}
        />
        Обкладинка
      </label>

      <button
        type="button"
        onClick={() => deleteExistingImage(image.id)}
      >
        Видалити
      </button>
    </div>
  </div>
))}

    {selectedFiles.map((item) => (
      <div className="photo-card" key={item.key}>
        <img src={item.preview} alt="Попередній перегляд" />

        <div className="photo-actions">
          <label>
            <input
              type="radio"
              name="cover"
              checked={coverSelection === item.key}
              onChange={() => setCoverSelection(item.key)}
            />
            Обкладинка
          </label>

          <button
            type="button"
            onClick={() => removeSelectedFile(item.key)}
          >
            Видалити
          </button>
        </div>
      </div>
    ))}
  </div>
</div>


        <button type="submit" disabled={saving}>
          {saving
            ? "Збереження..."
            : isEditing
              ? "Зберегти зміни"
              : "Створити оголошення"}
        </button>
      </form>
    </section>
  );
}

export default ListingForm;
