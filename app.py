from flask import Flask, render_template, request, jsonify, session
import smtplib
import random
import time
import os
import pyotp
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET') or 'fallback_secret'

# Email configuration
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

# Data stores
login_otps = {}
purchase_otps = {}
totp_secrets = {}

# Twilio configuration
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
verify_sid = os.getenv("TWILIO_VERIFY_SID")
client = Client(account_sid, auth_token) if account_sid and auth_token else None

def send_otp_email(to_email, otp):
    """Send OTP via email"""
    subject = "Your Verification Code"
    body = f"Your verification code is: {otp}\nValid for 1 minute."
    message = f"Subject: {subject}\n\n{body}"
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message)
        return True
    except Exception as e:
        app.logger.error(f"Email error: {str(e)}")
        return False

@app.route('/send_email_otp', methods=['POST'])
def send_email_otp():
    """Handle email OTP requests"""
    data = request.json
    email = data.get('email', '').strip().lower()
    
    if not email or '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    otp = f"{random.randint(100000, 999999)}"
    login_otps[email] = {
        'otp': otp,
        'timestamp': time.time()
    }

    if send_otp_email(email, otp):
        return jsonify({'message': 'OTP sent successfully'}), 200
    return jsonify({'error': 'Failed to send OTP'}), 500

@app.route('/verify_email_otp', methods=['POST'])
def verify_email_otp():
    """Verify email OTP"""
    data = request.json
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()

    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400

    record = login_otps.get(email)
    if not record:
        return jsonify({'error': 'OTP not found or expired'}), 400

    if time.time() - record['timestamp'] > 60:
        login_otps.pop(email, None)
        return jsonify({'error': 'OTP expired'}), 400

    if otp == record['otp']:
        login_otps.pop(email, None)
        session['user_email'] = email
        return jsonify({
            'message': 'OTP verified',
            'token': f"tok_{random.randint(1000, 9999)}"
        }), 200

    return jsonify({'error': 'Incorrect OTP'}), 400

@app.route('/send_phone_otp', methods=['POST'])
def send_phone_otp():
    data = request.json
    phone = data.get("phone")
    channel = data.get("channel", "sms")  # Default to SMS if not provided

    if not phone:
        return jsonify({"error": "Phone number is required"}), 400

    try:
        verification = client.verify.v2.services(verify_sid).verifications.create(
            to=phone,
            channel=channel
        )
        return jsonify({"status": verification.status, "sid": verification.sid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/verify_phone_otp', methods=['POST'])
def verify_phone_otp():
    data = request.json
    phone = data.get("phone")
    code = data.get("code")

    if not phone or not code:
        return jsonify({"error": "Phone number and code are required"}), 400

    try:
        verification_check = client.verify.v2.services(verify_sid).verification_checks.create(
            to=phone,
            code=code
        )
        return jsonify({"status": verification_check.status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route: generate TOTP QR
@app.route('/generate_otp_qr')
def generate_otp_qr():
    email = request.args.get('email')
    if not email or '@' not in email:
        return jsonify({'error': 'Invalid email'}), 400

    secret = pyotp.random_base32()
    totp_secrets[email] = secret
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=email, issuer_name="Email OTP Authenticator")
    return jsonify({'otp_uri': uri})

@app.route('/verify_totp', methods=['POST'])
def verify_totp():
    """Verify TOTP code"""
    data = request.json
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    secret = totp_secrets.get(email)

    if not secret:
        return jsonify({'error': 'TOTP not set up for this email'}), 400

    totp = pyotp.TOTP(secret)
    if totp.verify(code, valid_window=1):
        session['user_email'] = email
        return jsonify({
            'message': 'TOTP verified',
            'token': f"tok_{random.randint(1000, 9999)}"
        }), 200
    return jsonify({'error': 'Invalid TOTP code'}), 400

# Route: send purchase OTP
@app.route('/send_purchase_otp', methods=['POST'])
def send_purchase_otp():
    data = request.json
    email = data.get('email')
    method = data.get('method')
    if not email or '@' not in email or method not in ('card','gcash'):
        return jsonify({'error': 'Invalid purchase request'}), 400

    otp = f"{random.randint(100000, 999999)}"
    purchase_otps[email] = {'otp': otp, 'timestamp': time.time(), 'method': method}

    if send_otp_email(email, otp):
        return jsonify({'message': 'Purchase OTP sent'}), 200
    return jsonify({'error': 'Failed to send purchase OTP'}), 500

# Route: verify purchase OTP
@app.route('/verify_purchase_otp', methods=['POST'])
def verify_purchase_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')

    record = purchase_otps.get(email)
    if not record:
        return jsonify({'error': 'Purchase OTP expired or not found'}), 400

    if time.time() - record['timestamp'] > 60:
        purchase_otps.pop(email, None)
        return jsonify({'error': 'Purchase OTP expired'}), 400

    if otp == record['otp']:
        purchase_otps.pop(email, None)
        # mark user as premium
        if session.get('user_email') == email:
            session['is_premium'] = True
        return jsonify({'success': True}), 200

    return jsonify({'success': False}), 400

@app.route('/')
def index():
    """Main application route"""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)