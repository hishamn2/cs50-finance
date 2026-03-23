C$50 Finance
A full-stack stock trading simulator built with Python, Flask, and SQL. This application allows users to manage a virtual portfolio using live stock market data.

Technical Features
Real-time Data Integration: Fetches live stock prices using the IEX Cloud API.

Portfolio Management: Automatically calculates the total value of holdings based on current market prices and user cash balance.

Database Management: Uses SQL to maintain a complete audit trail of every buy and sell transaction.

Security: Implements password hashing via werkzeug.security and session-based authentication.

Custom Functionality: Includes a password update feature to demonstrate end-to-end user management.

Technical Stack
Backend: Flask (Python)

Database: SQLite3

Frontend: HTML5, CSS3, Bootstrap 5, Jinja2

API: IEX Cloud

Installation and Usage
Clone the repository to your local environment.

Install dependencies listed in requirements.txt.

Export your IEX API Key as an environment variable.

Run flask run to start the development server.
