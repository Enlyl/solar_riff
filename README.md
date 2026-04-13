# 🛰️ Solar Riff Engine v2.0

**[RU]** Генератор тяжелых риффов, управляемый солнечной активностью. Приложение конвертирует Kp-индекс от NOAA в темп, строй и ритм гитарного дисторшна в реальном времени.

**[EN]** Heavy riff generator driven by solar activity. It converts live NOAA Kp-index data into tempo, tuning, and rhythmic patterns for real-time guitar synthesis.

---

### 🛠️ Stack
* **Python:** Streamlit, Pandas, Plotly.
* **JS:** Web Audio API (Custom Distortion & Cabinet Sim).
* **Data Source:** NOAA Space Weather API.

### ⚡ Key Features / Особенности
* **Adaptive Tuning:** Автоматическая смена строя (Standard E ↔ Drop A) в зависимости от геомагнитного фона.
* **Neural Tone:** Браузерный синтез перегруженной гитары (sawtooth + multi-stage distortion).
* **Live Telemetry:** Визуализация играемых нот и аккордов в реальном времени.
* **Ghost UI:** Минималистичный темный интерфейс в стиле киберпанк.

### 🚀 Quick Start / Запуск
1. Установите зависимости:
   ```bash
   pip install streamlit pandas requests plotly
