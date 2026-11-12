import requests
import uuid

class PayPalError(Exception):
    pass

class PayPalService:
    def __init__(self, client_id, client_secret, base_url,
                 merchant_email="", return_url="", cancel_url=""):
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.base_url = base_url.rstrip("/")
        self.merchant_email = merchant_email.strip()
        self.return_url = return_url
        self.cancel_url = cancel_url

    def is_configured(self):
        return bool(self.client_id and self.client_secret)

    def _token(self):
        if not self.is_configured():
            raise PayPalError("PayPal credentials are missing. Add Sandbox Client ID and Secret to .env.")
        try:
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                timeout=25
            )
            if not response.ok:
                raise PayPalError(f"PayPal authentication failed ({response.status_code}): {response.text[:700]}")
            return response.json()["access_token"]
        except requests.RequestException as exc:
            raise PayPalError(f"Could not reach PayPal: {exc}") from exc

    def _headers(self, token, request_id=None):
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if request_id:
            headers["PayPal-Request-Id"] = request_id
        return headers

    def create_order(self, amount, currency, description, milestone_id):
        token = self._token()
        purchase_unit = {
            "reference_id": f"trustpay-milestone-{milestone_id}",
            "custom_id": f"trustpay-milestone-{milestone_id}",
            "description": description[:127],
            "amount": {
                "currency_code": currency,
                "value": f"{float(amount):.2f}"
            }
        }
        # Optional payee email. The receiving merchant must be eligible and configured.
        if self.merchant_email:
            purchase_unit["payee"] = {"email_address": self.merchant_email}

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [purchase_unit],
            "application_context": {
                "brand_name": "TrustPay AI Demo",
                "user_action": "PAY_NOW",
                "return_url": self.return_url,
                "cancel_url": self.cancel_url
            }
        }
        try:
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=self._headers(token, str(uuid.uuid4())),
                json=payload,
                timeout=30
            )
            if not response.ok:
                raise PayPalError(f"Create order failed ({response.status_code}): {response.text[:1000]}")
            data = response.json()
            approval = next((x["href"] for x in data.get("links", [])
                             if x.get("rel") in ("approve", "payer-action")), None)
            if not approval:
                raise PayPalError("PayPal created an order but did not return an approval link.")
            data["approval_url"] = approval
            return data
        except requests.RequestException as exc:
            raise PayPalError(f"PayPal request failed: {exc}") from exc

    def capture_order(self, order_id):
        token = self._token()
        try:
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers=self._headers(token, str(uuid.uuid4())),
                json={},
                timeout=30
            )
            if not response.ok:
                raise PayPalError(f"Capture failed ({response.status_code}): {response.text[:1000]}")
            return response.json()
        except requests.RequestException as exc:
            raise PayPalError(f"PayPal capture request failed: {exc}") from exc

    @staticmethod
    def extract_capture_id(capture_response):
        for unit in capture_response.get("purchase_units", []):
            for capture in unit.get("payments", {}).get("captures", []):
                if capture.get("id"):
                    return capture["id"]
        return None
