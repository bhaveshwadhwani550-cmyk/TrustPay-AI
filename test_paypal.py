
import os
from dotenv import load_dotenv
from paypal.service import PayPalService, PayPalError

# Load environment variables from .env
load_dotenv()

# Initialize PayPal Sandbox service
paypal = PayPalService(
    client_id=os.getenv("PAYPAL_CLIENT_ID", ""),
    client_secret=os.getenv("PAYPAL_CLIENT_SECRET", ""),
    base_url=os.getenv(
        "PAYPAL_BASE_URL",
        "https://api-m.sandbox.paypal.com"
    )
)

print("\n========== TRUSTPAY PAYPAL TEST ==========\n")

# Check credentials
if not paypal.is_configured():
    print("FAILED: PayPal credentials are missing.")
    print("Check your .env file.")
else:
    print("Credentials detected.")
    print("Sandbox URL:", paypal.base_url)

    try:
        # Request OAuth access token
        token = paypal._token()

        if token:
            print("\nSUCCESS!")
            print("PayPal Sandbox authentication completed.")
            print("OAuth access token received.")
            print("Token length:", len(token))
            print("Your credentials are working.")

    except PayPalError as error:
        print("\nPAYPAL CONNECTION FAILED")
        print("Error:", error)

    except Exception as error:
        print("\nUNEXPECTED ERROR")
        print(type(error).__name__, str(error))

print("\n==========================================")
