# 🎓 University Feedback System

A full-stack web application with a **Flask (Python) backend** and a pure **HTML/CSS/JavaScript frontend** for collecting and analyzing student feedback using NLP-based sentiment analysis.

---

## 🛠 Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Python · Flask · SQLite             |
| Frontend  | HTML5 · CSS3 · JavaScript   |
| NLP/ML    | scikit-learn (TF-IDF + Logistic Regression) |
| Charts    | Chart.js (CDN)                      |

---

## 📁 Project Structure

```
feedback-web/
├── app.py                  # Flask backend — routes, auth, API
├── requirements.txt
├── data/
│   ├── feedback.db         # SQLite database (auto-created)
│   └── feedback_dataset.csv
├── model/
│   ├── model.pkl           # Trained sentiment model
│   └── vectorizer.pkl      # TF-IDF vectorizer
├── static/
│   ├── css/style.css       # All styles
│   └── js/
│       ├── login.js        # Login page logic
│       └── dashboard.js    # Dashboard logic (all roles)
└── templates/
    ├── login.html          # Login page
    └── dashboard.html      # Dashboard (student/teacher/admin)
```

---

## 🚀 Getting Started

### 1. Clone & enter the project
```bash
git clone https://github.com/YOUR_USERNAME/feedback-web.git
cd feedback-web
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```

Open your browser at **http://localhost:5000**

> The database is auto-created and seeded with default users on first run.

---

## 🔑 Default Credentials

| Role    | Username            | Password |
|---------|---------------------|----------|
| Student | `student1`          | `123`    |
| Student | `student2`          | `123`    |
| Teacher | `VENKATARAMANA V`   | `123`    |
| Teacher | `SHENDE AMIT`       | `123`    |
| Teacher | `PRAVEEN`           | `123`    |
| Admin   | `admin`             | `123`    |

---

## ✨ Features

**Student**
- Browse available courses and faculty
- Submit feedback with star rating
- Instant AI sentiment detection

**Teacher**
- Personal dashboard with metrics
- Rating and sentiment charts
- Full feedback history

**Admin**
- System-wide analytics
- Faculty performance comparison
- Search and filter all feedback
- Export data as CSV

---

## 🧠 NLP Model

- Vectorizer: TF-IDF (bigrams, 5000 features)
- Classifier: Logistic Regression
- Labels: `1` = Positive, `0` = Negative

To retrain the model, update `data/feedback_dataset.csv` and run:
```bash
python scripts/train_model.py   # if you have the scripts folder
```

---

## 📄 License

MIT License
