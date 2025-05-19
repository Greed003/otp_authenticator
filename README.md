#OTP Authenticator

A secure One-Time Password (OTP) authentication system built with Flask (Python backend) and HTML/CSS/JavaScript frontend.

## Features

- OTP generation and verification
- Responsive design with smooth transitions
- 1 minutes OTP expiration 
- 30 second timer for resend functionality
- Persistent login session using localStorage
- Error handling and validation
- Simple dashboard with subscription

## Prerequisites

- Python 3.6+
- Flask
- smtplib (for sending emails included in Python)
- A Gmail account (for sending OTP emails)
- twilio

## Setup Instructions

### 1. Clone Github

git clone https://github.com/Greed003/otp_authenticator.git

### 2. Install dependencies

pip install flask python-dotenv pyotp twilio

### 3. Configure email settings

Edit .env file with your email credentials:  
SENDER_EMAIL = 'your.email@gmail.com'  
SENDER_PASSWORD = 'your_password_or_app_specific_password'  
TWILIO_ACCOUNT_SID='your twilio account sid'  
TWILIO_AUTH_TOKEN='your twilio authentication token'  
TWILIO_VERIFY_SID='your twilio verify sid'  

### 4. Run the application
python app.py

### 5. Access the application
Open your browser and navigate to: http://localhost:5000

## Usage Flow

### 1. Welcome Screen
Click "Get Started" to begin

### 2. Email Input
Enter your email address
Click "Send OTP"

### 3. OTP Verification
Enter the 6-digit code sent to your email or phone  
OTP expires in 1 minutes  
Can resend OTP after 30 seconds  

### 4. Success Screen
Authentication successful  
Continue to dashboard

### 5. Home Screen
View description about otp  
Logout option  
Purchase Subscription  