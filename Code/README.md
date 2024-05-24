Library Management System

The Library Management System project, aesthetically crafted, earned a perfect score of 100 marks at IITM.

Overview:
The Library Management System is a web-based application that allows administrators to perform CRUD operations on sections and books, manage user requests, and track book statistics. Users can request and return books, search for books by author name, section name, and book name. Access to books is granted by the admin upon request approval.

Setup Instructions:
Clone the Repository:

#bash
git clone <repository_url>
cd library-management-system
Setup Virtual Environment:

#bash
python3 -m venv venv
source venv/bin/activate  # Activate virtual environment (Linux/Mac)
.\venv\Scripts\activate    # Activate virtual environment (Windows)
Copy .env.sample to .env:

#bash
cp .env.sample .env
Add Secret Key to .env:

Open the .env file and add your secret key:
SECRET_KEY=your_secret_key_here
Install Required Libraries:


pip install -r requirements.txt
Start Flask Server:
flask run

Admin Login:
Username: admin
Password: admin
Additional Information:

User Access:
Users can view their requests and the books they have.
Access to books is granted by the admin upon request approval.

Admin Access:
Admins can view the total sections and books in the system.
They can accept, decline, and revoke access from users.

This guide provides clear instructions for setting up and running the Library Management System. If you have any questions or need further assistance, feel free to ask!
