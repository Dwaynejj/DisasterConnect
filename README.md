# 🚨 DisasterConnect

> A powerful, modern, and feature-rich Desktop Application for Disaster and Emergency Response Management.

**DisasterConnect** is a comprehensive Python desktop application built with PyQt5 and MongoDB. It empowers emergency responders, administrators, and dispatchers to visualize critical incidents, allocate resources, and manage operations in real-time.

---

## ✨ Key Features

### 🛡️ Secure Authentication
- **Role-Based Access Control:** Differentiates between Responders, Dispatchers, and Administrators.
- **Robust Security:** Passwords hashed via `bcrypt` and session management using `PyJWT`.
- **Validation:** Enforced password strength and secure credential checks.

### 🗺️ Interactive Maps & Geography
- **Live Folium Integration:** Uses `PyQtWebEngine` to render highly interactive maps seamlessly within the desktop interface.
- **Incident Heatmaps:** Visualize incident density and severity dynamically.
- **Location Picker:** Drop pins on the map to accurately log coordinates for new incidents and resources.

### 📋 Incident & Resource Management
- **Dashboard Overview:** At-a-glance metrics for active emergencies and available resources.
- **Bulk Actions:** Select multiple incidents or resources simultaneously to perform bulk updates, deletions, or CSV exports.
- **Flexible Views:** Toggle between clean Table List views and modern Grid Card views for resource tracking.

### 🎨 Beautiful, Modern UI
- **Custom Design System:** Built from the ground up with a custom Qt Stylesheet (QSS) implementation.
- **Theming:** Full support for Dynamic Light Mode, Dark Mode, and System Default syncing.
- **Accent Colors:** Personalize the application with 6 custom primary color swatches (Blue, Green, Red, Amber, Purple, Cyan).
- **Responsive Animations:** Fluid slide-in drawers and hover effects for a premium native feel.

---

## 🛠️ Technology Stack

- **Frontend Interface:** [PyQt5](https://pypi.org/project/PyQt5/) & `PyQtWebEngine`
- **Mapping Engine:** [Folium](https://python-visualization.github.io/folium/) & Leaflet.js
- **Database:** [MongoDB](https://www.mongodb.com/) (`pymongo`)
- **Security:** `bcrypt` & `PyJWT`
- **Styling:** Custom QSS (Qt Stylesheets)

---

## 🚀 Setup & Installation

### 1. Prerequisites
- **Python 3.8+** installed on your system.
- A running **MongoDB** instance (Local or Atlas).

### 2. Clone the Repository
```bash
git clone https://github.com/Dwaynejj/DisasterConnect.git
cd DisasterConnect
```

### 3. Create a Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory and populate it with your MongoDB connection string and a secret key:

```env
MONGODB_URI=mongodb://localhost:27017/  # Or your MongoDB Atlas URI
MONGODB_DATABASE=disaster_connect
SECRET_KEY=your_super_secret_jwt_key_here
```

*(Note: You can use `.env.example` as a template).*

### 6. Run the Application
```bash
python main.py
```

---

## 📸 Screenshots & Usage

- **Dashboard:** Instantly see your map heatmaps and KPIs.
- **Incidents Tab:** Track severity levels (Low, Medium, High, Critical) and update status (Active, Resolved, Under Review).
- **Settings:** Head over to the Settings tab to switch on **Dark Mode** and pick your favorite accent color!

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Dwaynejj/DisasterConnect/issues).

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
