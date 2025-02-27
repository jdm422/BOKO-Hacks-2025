# BokoHacks 2025
An Application Security Challenge Platform for Texas State University's 2025 BokoHacks

## Overview
This project is a deliberately vulnerable web application designed to help students learn about common web security vulnerabilities through hands-on practice. It includes various challenges focusing on SQL injection, XSS (Cross-Site Scripting), access control vulnerabilities, and authentication bypass techniques.

## Requirements
- Python 3.8 or higher → [Download Python](https://www.python.org/downloads/)
- Pip (Python package installer)
- SQLite → [Download SQLite](https://www.sqlite.org/download.html) (Optional if you want binaries otherwise; dependencies should install automatically)
- Modern web browser (Chrome/Firefox recommended)
- Text editor or IDE (VS Code recommended)

## Setup Instructions
1. Clone the repository:
```bash
git clone https://github.com/Nick4453/Boko-Hacks-2025.git
cd boko-hacks-2025
```

2. Create and activate a virtual environment (recommended): (You can also do this through VS Code)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database: (You may not need to do this step; if it doesn't work, check that your env path is correct)
```bash
python -c "from app import app, setup_database; app.app_context().push(); setup_database()"
```

5. Start the application: 
```bash
python app.py
```

6. Open http://localhost:5000 in your browser

## Learning Resources
If you're new to web application security testing, here are some resources to help you understand the vulnerabilities you might encounter:

1. [OWASP Top 10](https://owasp.org/www-project-top-ten/) - The standard awareness document for web application security
2. [PortSwigger Web Security Academy](https://portswigger.net/web-security) - Free, online web security training
3. [SQL Injection Cheat Sheet](https://portswigger.net/web-security/sql-injection/cheat-sheet)
4. [XSS Cheat Sheet](https://portswigger.net/web-security/cross-site-scripting/cheat-sheet)
5. [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) - A list of useful payloads for bypassing security controls

## Development Notes
- The application uses Flask for the backend
- SQLite databases store application data
- Frontend uses vanilla JavaScript and CSS
- All vulnerabilities are intentional for educational purposes

## Security Notice
This application contains intentional security vulnerabilities for educational purposes. DO NOT:
- Use real credentials or sensitive information while testing
- Deploy this application on a public network or server
- Use techniques learned here against real websites without explicit permission

## License
MIT License - See LICENSE file for details
