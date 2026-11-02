# NutriScan AI

### AI-Powered Food Nutrition Analysis System

NutriScan AI is a web-based application that helps users understand the nutritional value of food products through barcode scanning and AI-powered nutritional analysis.

Users can scan food product barcodes, view nutritional information, receive AI-generated summaries, compare products and maintain their personal scan history.

## Features

- **User Authentication:** Registration, login and logout functionality.
- **Barcode Scanning:** Scan products using a live camera.
- **Image Upload:** Upload barcode images for product identification.
- **Manual Barcode Entry:** Enter product barcodes manually.
- **Nutrition Analysis:** View calories, protein, carbohydrates, fat, fibre, sugar, saturated fat and sodium.
- **AI-Powered Summary:** Get nutritional insights using Google Gemini AI.
- **Nutrition Score:** Evaluate products using a simple nutritional scoring system.
- **Product Comparison:** Compare two previously scanned products.
- **Scan History:** Save and manage previously scanned products.
- **Dashboard:** View scan statistics and nutrition analytics.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| HTML | Webpage structure |
| CSS | Styling |
| JavaScript | Frontend functionality |
| SQLite | Database |
| Open Food Facts API | Product and nutrition information |
| Google Gemini API | AI-generated nutritional summaries |
| Chart.js | Data visualization |
| html5-qrcode | Barcode scanning |

## Project Structure

```text
NutriScan-AI/
│
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   ├── scan.html
│   ├── compare.html
│   ├── history.html
│   ├── login.html
│   └── register.html
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Manvi-Kaintura/NutriScan-AI.git
```

### 2. Open the project folder

```bash
cd NutriScan-AI
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the project root directory.

Add:

```env
GEMINI_API_KEY=your_gemini_api_key
FLASK_SECRET_KEY=your_secret_key
```

Obtain your Gemini API key from Google AI Studio.

Generate a secure Flask secret key using:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Never share or upload your `.env` file.

### 7. Run the application

```bash
python app.py
```

Open your browser and visit:

http://127.0.0.1:5000

## Nutrition Scoring

NutriScan AI uses a simple heuristic-based scoring system to evaluate food products based on available nutritional information.

The score considers:

- Sugar
- Saturated fat
- Sodium
- Fibre
- Protein
- Calories

The score ranges from 1 to 10.

**Note:** The scoring system is an educational project feature and is not a medically validated nutritional assessment.

## Data Source

Product information is retrieved from the Open Food Facts API.

AI-generated nutritional summaries are powered by Google Gemini.

## Future Improvements

- Improved nutritional analysis.
- Additional food database integrations.
- Enhanced user experience.
- More detailed nutritional insights.

## Author

**Manvi Kaintura**

GitHub: https://github.com/Manvi-Kaintura

---

*NutriScan AI – Making food choices more informed through technology.*