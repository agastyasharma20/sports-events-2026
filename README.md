# 🏆 Sports Events 2026 — PIEMR Indore
**Full-Stack Web Application | Python Flask + SQLite**

---

## 📁 Project Structure
```
sports_app/
├── app.py                  # Flask backend (all API routes)
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── static/
    └── index.html          # Full multi-page frontend
```

---

## 🚀 Setup & Run

### Step 1 — Install Python (if not already)
Download from https://www.python.org/downloads/

### Step 2 — Install Dependencies
Open terminal in the `sports_app` folder and run:
```bash
pip install -r requirements.txt
```

### Step 3 — Start the Server
```bash
python app.py
```

### Step 4 — Open in Browser
Visit: **http://localhost:5000**

---

## 🌐 Pages
| Page | Description |
|------|-------------|
| **Home** | Hero banner, sports grid, coordinators, CTA |
| **About** | Event details, eligibility, rules |
| **Schedule** | Day-wise event timetable (23–29 March) |
| **Register** | Student registration form |
| **Contact** | Email, address, query hours, map |
| **Admin** | Password-protected dashboard |

---

## 🔐 Admin Panel
- URL: Click **Admin** in navbar
- Password: `sports2026`
- Features: View all registrations, filter by event/year, search, delete entries, export CSV

---

## 🔌 API Endpoints
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/register` | Submit registration |
| POST | `/api/admin/login` | Admin login |
| POST | `/api/admin/logout` | Admin logout |
| GET | `/api/admin/registrations` | Get all registrations (with filters) |
| GET | `/api/admin/stats` | Dashboard stats |
| DELETE | `/api/admin/delete/<id>` | Delete a registration |
| GET | `/api/admin/export` | Download CSV |

---

## 🗄️ Database
- Uses **SQLite** (`sports_registrations.db`) — auto-created on first run
- No external database setup needed

---

## 📦 Tech Stack
- **Backend**: Python 3, Flask, Flask-SQLAlchemy, Flask-CORS
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Fonts**: Bebas Neue, Barlow Condensed (Google Fonts)

---

*Designed & Developed by Agastya Sharma*
*© 2026 PIEMR Indore*
