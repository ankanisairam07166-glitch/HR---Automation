 HR Automation Platform (Phase 1-3)

This repository contains all project phases for the HR Automation System, including backend scripts, frontend interface, and setup scripts for resume processing and recruitment workflows.

The back, hr-frontend files are original which are final versions. 

## 📁 Final Project Structure

```
hr-automation-system/         # (your project root)
├── .gitignore                # Git ignore rules
├── README.md                 # Project overview & setup guide
├── requirements.txt          # Python dependencies (for back/)
│
├── back/                     # Final backend
│   ├── backend.py
│   ├── db.py
│   ├── scraper.py
│   ├── diagnosis_tool.py
│   ├── testlify-integration.py
│   ├── postman_python_script.py
│   ├── email_util.py
│   ├── tasks.py
│   ├── assessment_links/
│   ├── resumes/
│   ├── logs/
│   └── [other required .json, .html, .png]
│
├── hr-frontend/              # Final frontend (React + Tailwind)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   └── services/
│   ├── package.json
│   ├── tailwind.config.js
│   └── postcss.config.js
```

HR Automation System

This repository contains the **finalized backend and frontend** of the HR Automation System – designed for resume parsing, candidate evaluation, automation with Testlify and BambooHR, and a modern UI dashboard.



## 🚀 Project Structure

- `back/` – Python-based backend for automation, scraping, parsing, email handling, and resume evaluation.
- `hr-frontend/` – React + TailwindCSS frontend for user interaction, dashboards, and screening flow.



## 🛠 Backend Setup (`back/`)

In terminal
python -m venv venv
venv\Scripts\activate                  # On Windows
pip install -r requirements.txt
python back/backend.py                # Or your main entry script

## Frontend Setup (hr-frontend/)
cd hr-frontend
npm install
npm run dev                           # or npm start

##  Tech Used
Backend: Python, Automation Scripts, Testlify API, BambooHR

Frontend: React, TailwindCSS

Tools: Email handling, Resume parsing, Job assessment logic
"# HR-Automaticn"  "# HR-Automaticn" 
