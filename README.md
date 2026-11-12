# TrustPay AI

**AI-assisted milestone evidence review and human-approved PayPal payments.**

TrustPay AI is a hackathon prototype for freelancers and clients. It organizes projects into milestones, reviews submitted text evidence against agreed requirements, and lets a client create a PayPal Sandbox checkout after approving a milestone.

## Important scope and safety notes

- This prototype is **not an escrow service** and does not hold funds.
- AI findings are advisory. The client must inspect and approve work.
- PayPal Sandbox only is recommended during development.
- The role selector is a demo convenience, not secure authentication.
- Do not use this prototype to process real customer payments.
- Do not commit `.env`, credentials, database files or private submissions.

## Features

- Create projects with client/freelancer names, budget and currency.
- Add milestones with requirements, amount and due date.
- Submit text evidence (or `.txt` / `.md` evidence files).
- AI review using an OpenAI-compatible chat completion, if configured.
- Clearly-labelled keyword heuristic fallback when no LLM key is configured.
- Client review, approval and revision request.
- PayPal Orders v2 Sandbox create-order and capture flow.
- SQLite storage and activity feed.

## 1. Requirements

- Python 3.10 or newer
- VS Code
- Internet connection for AI and PayPal API calls

## 2. Install

Open this folder in VS Code, then open Terminal:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
venv\Scripts\activate.bat
```

Install packages:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configure environment

Copy `.env.example` to `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Add credentials only when ready:
- `OPENAI_API_KEY` to enable LLM-based milestone review.
- `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` from your PayPal Developer Sandbox app.

Keep `.env` private. It is excluded by `.gitignore`.

Without an LLM key, the app uses a basic keyword heuristic clearly labelled `DEMO_HEURISTIC`. This is not AI verification and should not be presented as an AI model in the hackathon demo.

## 4. Run

```bash
streamlit run app.py
```

Open the local URL Streamlit prints, normally `http://localhost:8501`.

The SQLite database `trustpay.db` is created automatically on first run.

## 5. Test the app without PayPal

1. Create a project.
2. Add a milestone with clear requirements.
3. Switch to Freelancer in the sidebar.
4. Submit evidence text.
5. Inspect the AI review (LLM mode if configured; otherwise demo heuristic).
6. Switch to Client.
7. Approve the milestone or request a revision.

## 6. PayPal Sandbox setup

1. Open https://developer.paypal.com/
2. Sign in and open the Developer Dashboard.
3. Find Apps & Credentials and select Sandbox.
4. Create or select a Sandbox REST app.
5. Copy its Client ID and Secret into `.env`.
6. Use the Sandbox Business merchant account and Sandbox Personal buyer account shown in your developer dashboard.
7. Restart Streamlit after editing `.env`.
8. Create a project and milestone. Switch to Client and approve it.
9. Open Payments and click **Create PayPal checkout order**.
10. Click **Open PayPal Sandbox Checkout** and sign in using the Sandbox Personal buyer account.
11. Complete checkout.
12. Return to the TrustPay app and click **I approved checkout – capture payment**.
13. Confirm that the payment status changes to `COMPLETED`.

The capture action is a server-to-server PayPal API request. PayPal should only accept it after the buyer has approved the order. The app uses PayPal's Sandbox API base URL by default.

If your sandbox app requires a specific merchant/payee configuration, set `PAYPAL_MERCHANT_EMAIL` to the sandbox merchant email. The receiving account must be eligible to receive the transaction.

## 7. AI setup

Set `OPENAI_API_KEY` in `.env`. The default model is `gpt-4o-mini`; change `OPENAI_MODEL` if your account uses a different available model. Restart Streamlit.

The AI compares milestone requirements with evidence text and returns:
- supported requirements
- missing/unclear evidence
- confidence estimate
- recommendation
- explanation

The confidence is a model estimate, not a guarantee. It is not proof that software works. The client remains responsible for inspecting the deliverable and approving the milestone.

## 8. Known prototype limitations

- No real user accounts, login, or access-control enforcement.
- Evidence file extraction currently supports `.txt` and `.md` only.
- No verified PayPal webhook receiver is included in this local Streamlit prototype.
- The demo captures the order after the buyer returns from PayPal checkout. For production, verify the order state, payer, merchant, currency and amount server-side before capture, and reconcile payment status using verified PayPal webhooks.
- Payment records are stored locally in SQLite.
- No escrow, automatic dispute resolution, refunds, split payouts or marketplace onboarding.
- For a public multi-user deployment, use a proper backend, authentication, secure file storage, database backups and webhook signature verification.

## 9. Suggested hackathon demo

1. Create a website project with three milestones.
2. Submit evidence for one milestone.
3. Show the AI's requirement-by-requirement assessment.
4. Switch to Client and approve the milestone.
5. Create a PayPal Sandbox checkout order.
6. Complete buyer approval in the PayPal Sandbox.
7. Capture the order and show the updated payment record.

## Technology

Python · Streamlit · SQLite · OpenAI API (optional) · PayPal REST Orders v2 · pandas

## License

MIT. See `LICENSE`.
