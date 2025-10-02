import random


def generate_otp():
    return "123456"
    # return str(random.randint(100000, 999999))


def send_otp_message(phone: str, otp: str):
    # Stub: Integrate SMS provider (Twilio, AWS SNS, etc.)
    print(f"📲 Sending OTP {otp} to {phone}")
