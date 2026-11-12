# TrustPay AI

**AI-assisted milestone evidence review and human-approved PayPal payments.**

TrustPay AI is a hackathon prototype for freelancers and clients. It organizes projects into milestones, reviews submitted evidence against agreed requirements using a locally running AI model, and lets a client create a PayPal Sandbox checkout after approving a milestone.

## Important Scope and Safety Notes

- This prototype is **not an escrow service** and does not hold funds.
- AI findings are advisory. The client must inspect and approve the actual work.
- PayPal Sandbox only is recommended during development.
- The role selector is a demo convenience, not secure authentication.
- Do not use this prototype to process real customer payments.
- Never commit `.env`, credentials, database files or private submissions.

## Features

- Create projects with client/freelancer names, budget and currency.
- Add milestones with requirements, amount and due date.
- Submit text evidence or `.txt` / `.md` evidence files.
- AI-powered milestone evidence review using Ollama and Qwen 2.5 1.5B.
- Requirement-by-requirement assessment of submitted evidence.
- Client review, milestone approval and revision requests.
- PayPal Orders v2 Sandbox create-order and capture flow.
- SQLite database storage and activity feed.

## 1. Requirements

- Python 3.10 or newer
- VS Code (recommended)
- Ollama
- Internet connection for PayPal Sandbox API calls

## 2. Install the Project

Clone the repository:

```bash
git clone https://github.com/bhaveshwadhwani550-cmyk/TrustPay-AI.git
cd TrustPay-AI
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

On Windows Command Prompt:

```bat
venv\Scripts\activate.bat
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configure Ollama and Qwen

Download and install Ollama from:

https://ollama.com/download

Download the Qwen 2.5 1.5B model:

```bash
ollama pull qwen2.5:1.5b
```

Make sure the Ollama service is running before starting the application.

The project uses the following AI configuration:

```env
TRUSTPAY_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

The model runs locally through Ollama, so an OpenAI API key is not required for this configuration.

## 4. Configure Environment Variables

Copy `.env.example` to `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure the relevant variables:

```env
TRUSTPAY_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b

PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com

PAYPAL_RETURN_URL=http://localhost:8501/?paypal=return
PAYPAL_CANCEL_URL=http://localhost:8501/?paypal=cancel
```

Replace the PayPal placeholders with your own Sandbox application credentials.

Keep `.env` private. It is excluded by `.gitignore`.

Restart Streamlit after changing environment variables.

## 5. Run the Application

From the project root directory, with your virtual environment activated:

```bash
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, normally:

http://localhost:8501

The SQLite database `trustpay.db` is created automatically when the application initializes.

## 6. Test the Application

1. Create a project.
2. Add a milestone with clear, specific requirements.
3. Switch to Freelancer in the sidebar.
4. Submit completed-work evidence.
5. Run the AI review and inspect its requirement-by-requirement assessment.
6. Switch to Client.
7. Inspect the submitted evidence and AI recommendation.
8. Approve the milestone or request a revision.

Remember that an AI recommendation is not independent proof that the submitted work is correct.

## 7. PayPal Sandbox Integration

1. Visit https://developer.paypal.com/
2. Sign in and open the Developer Dashboard.
3. Navigate to Apps & Credentials and select Sandbox.
4. Create or select a Sandbox REST application.
5. Copy its Client ID and Secret into `.env`.
6. Use a Sandbox Business merchant account and Sandbox Personal buyer account.
7. Restart Streamlit after editing `.env`.
8. Create a project and milestone.
9. Switch to Client and approve the milestone.
10. Open Payments and click **Create PayPal checkout order**.
11. Click **Open PayPal Sandbox Checkout**.
12. Sign in using the Sandbox Personal buyer account and complete checkout.
13. Return to TrustPay AI.
14. Click **I approved checkout – capture payment** after buyer approval.
15. Confirm that the payment status changes to `COMPLETED`.

The application uses PayPal's Sandbox Orders v2 API. The capture operation is a server-to-server API request.

For production use, verify the order state, payer, merchant, currency and amount server-side before capture, and reconcile payment status using verified PayPal webhooks.

## 8. AI Review System

TrustPay AI uses **Ollama with Qwen 2.5 1.5B** for local AI-assisted milestone evidence review.

The AI compares agreed milestone requirements with the freelancer's submitted evidence and generates:

- Supported requirements
- Missing or unclear evidence
- Confidence estimate
- Review recommendation
- Explanation of the assessment

The confidence value is a model estimate, not a guarantee of correctness. The AI does not independently test the submitted deliverable. The client remains responsible for inspecting and approving the actual work.

## 9. Known Prototype Limitations

- No real user accounts, login or access-control enforcement.
- Evidence file extraction currently supports `.txt` and `.md` only.
- No verified PayPal webhook receiver is included in this local Streamlit prototype.
- Payment capture is initiated manually after the buyer returns from PayPal checkout.
- Payment records are stored locally in SQLite.
- No escrow, automatic dispute resolution, refunds, split payouts or marketplace onboarding.
- AI assessments can be incorrect and require human review.
- A public multi-user deployment would require a proper backend, authentication, secure file storage, database backups and webhook signature verification.

## 10. Suggested Hackathon Demo

1. Create a website development project with multiple milestones.
2. Submit evidence for one milestone.
3. Demonstrate the Qwen-powered requirement-by-requirement AI assessment.
4. Switch to Client and inspect the submitted evidence.
5. Approve the milestone.
6. Create a PayPal Sandbox checkout order.
7. Complete buyer approval in PayPal Sandbox.
8. Capture the order and demonstrate the updated payment record.

## Technology Stack

- **Programming Language:** Python
- **Frontend:** Streamlit
- **Database:** SQLite
- **AI Runtime:** Ollama
- **AI Model:** Qwen 2.5 1.5B
- **Payment Integration:** PayPal REST API – Orders v2

## License

MIT License. See `LICENSE` for details.
