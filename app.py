import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from database import (
    init_db, create_project, list_projects, get_project, add_milestone,
    list_milestones, get_milestone, add_submission, list_submissions,
    save_verification, get_latest_verification, update_milestone_status,
    create_payment_record, update_payment_order, update_payment_capture,
    list_payments, get_payment_by_id, add_activity, get_activity
)
from ai.agent import verify_milestone
from paypal.service import PayPalService, PayPalError

load_dotenv()
st.set_page_config(page_title="TrustPay AI", page_icon="🛡️", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>

/* Main application text */
.stApp {
    background-color: #F5F7FB;
    color: #172033;
}

/* All headings */
h1, h2, h3, h4, h5, h6 {
    color: #14213D !important;
}

/* Form labels */
.stApp label,
.stApp [data-testid="stWidgetLabel"] p {
    color: #25324A !important;
    font-weight: 600 !important;
}

/* Input fields */
.stApp input,
.stApp textarea,
.stApp [data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #172033 !important;
}

/* Input placeholder */
.stApp input::placeholder,
.stApp textarea::placeholder {
    color: #8490A3 !important;
}

/* Normal text */
.stApp p,
.stApp li,
.stApp span {
    color: inherit;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #101B35 !important;
}

[data-testid="stSidebar"] * {
    color: #F7F9FF !important;
}

    .stApp { background: #f5f7fb; }
    [data-testid="stSidebar"] { background: #101b35; }
    [data-testid="stSidebar"] * { color: #f7f9ff !important; }
    .hero {
        background: linear-gradient(120deg, #101b35 0%, #1e3a68 100%);
        padding: 26px 30px; border-radius: 18px; color: white;
        margin-bottom: 18px;
    }
    .hero h1 { color: white; margin: 0; font-size: 2.15rem; }
    .hero p { color: #dce7ff; margin: 8px 0 0 0; }
    .metric-card {
        background: white; border: 1px solid #e6eaf2; border-radius: 14px;
        padding: 17px 18px; min-height: 105px;
    }
    .metric-label { color: #69758b; font-size: .86rem; }
    .metric-value { color: #14213d; font-size: 1.7rem; font-weight: 750; }
    .small-muted { color: #6b7280; font-size: .86rem; }
    div[data-testid="stForm"] { background: white; padding: 18px; border-radius: 14px; }
    .stButton button { border-radius: 9px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

init_db()

def money(amount, currency="USD"):
    try:
        return f"{currency} {float(amount):,.2f}"
    except Exception:
        return f"{currency} {amount}"

def paypal_service():
    return PayPalService(
        client_id=os.getenv("PAYPAL_CLIENT_ID", ""),
        client_secret=os.getenv("PAYPAL_CLIENT_SECRET", ""),
        base_url=os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com"),
        merchant_email=os.getenv("PAYPAL_MERCHANT_EMAIL", ""),
        return_url=os.getenv("PAYPAL_RETURN_URL", "http://localhost:8501/?paypal=return"),
        cancel_url=os.getenv("PAYPAL_CANCEL_URL", "http://localhost:8501/?paypal=cancel"),
    )

def get_selected_project_id():
    projects = list_projects()
    if not projects:
        return None, None
    options = {f"#{p['id']} · {p['title']}": p["id"] for p in projects}
    label = st.selectbox("Select project", list(options.keys()), key="project_selector")
    return options[label], get_project(options[label])

def metric(label, value, help_text=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="small-muted">{help_text}</div></div>',
        unsafe_allow_html=True
    )

def status_badge(status):
    mapping = {
        "PAID": "🟢 Paid", "APPROVED": "🔵 Approved",
        "SUBMITTED": "🟠 Submitted", "IN_PROGRESS": "🟣 In progress",
        "NEEDS_REVISION": "🔴 Needs revision", "PENDING": "⚪ Pending",
        "ORDER_CREATED": "🟠 Awaiting PayPal checkout",
        "COMPLETED": "🟢 Completed"
    }
    return mapping.get(status, status.replace("_", " ").title())

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🛡️ TrustPay AI")
    st.caption("Milestone verification & payments")
    role = st.radio("Demo role", ["Freelancer", "Client"], help="Demo-only role switcher. It is not secure authentication.")
    page = st.radio(
        "Navigation",
        ["Dashboard", "Projects & Milestones", "Submit Work & AI Review", "Approvals", "Payments", "About & Setup"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("Prototype · PayPal Sandbox")
    st.caption("Never use real payment credentials in this demo.")

# ---------- Header ----------
st.markdown(
    '<div class="hero"><h1>TrustPay AI</h1>'
    '<p>Clear milestones. Evidence-led reviews. Human-approved payments.</p></div>',
    unsafe_allow_html=True
)

# ---------- Dashboard ----------
if page == "Dashboard":
    projects = list_projects()
    milestones = [m for p in projects for m in list_milestones(p["id"])]
    payments = list_payments()
    paid = sum(float(p["amount"]) for p in payments if p["status"] == "COMPLETED")
    waiting = sum(1 for m in milestones if m["status"] in ("SUBMITTED", "APPROVED"))
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric("Projects", len(projects), "Created in this demo")
    with c2: metric("Milestones", len(milestones), "Across all projects")
    with c3: metric("Awaiting review/payment", waiting, "Submitted or approved")
    with c4: metric("Captured payments", money(paid), "Sandbox captures only")
    st.subheader("Your projects")
    if projects:
        rows = []
        for p in projects:
            ms = list_milestones(p["id"])
            paid_count = sum(1 for m in ms if m["status"] == "PAID")
            rows.append({
                "Project": p["title"], "Client": p["client_name"],
                "Freelancer": p["freelancer_name"], "Milestones": len(ms),
                "Paid": paid_count, "Budget": money(p["total_amount"], p["currency"]),
                "Status": p["status"]
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No projects yet. Open Projects & Milestones to create your first project.")
    st.subheader("Recent activity")
    activity = get_activity(10)
    if activity:
        for a in activity:
            st.write(f"**{a['created_at']}** · {a['message']}")
    else:
        st.caption("Your project activity will appear here.")

# ---------- Projects and milestones ----------
elif page == "Projects & Milestones":
    st.subheader("Create a project")
    with st.form("create_project_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Project title", placeholder="Website development")
            client_name = st.text_input("Client name", placeholder="Alex Morgan")
        with col2:
            freelancer_name = st.text_input("Freelancer name", placeholder="Sam Taylor")
            currency = st.selectbox("Currency", ["USD", "INR", "EUR", "GBP"])
        description = st.text_area("Project description", placeholder="Describe the agreed work...")
        total_amount = st.number_input("Total project budget", min_value=0.01, value=100.00, step=10.0)
        submitted = st.form_submit_button("Create project", type="primary")
        if submitted:
            if not title.strip() or not client_name.strip() or not freelancer_name.strip():
                st.error("Please enter the project title, client and freelancer.")
            else:
                pid = create_project(title.strip(), description.strip(), client_name.strip(),
                                     freelancer_name.strip(), float(total_amount), currency)
                add_activity(pid, f"Project '{title}' created.")
                st.success(f"Project #{pid} created.")
                st.rerun()

    st.divider()
    st.subheader("Add a milestone")
    projects = list_projects()
    if not projects:
        st.info("Create a project first.")
    else:
        pmap = {f"#{p['id']} · {p['title']}": p for p in projects}
        selected_label = st.selectbox("Choose project for milestone", list(pmap.keys()))
        project = pmap[selected_label]
        existing = list_milestones(project["id"])
        allocated = sum(float(m["amount"]) for m in existing)
        remaining = max(0, float(project["total_amount"]) - allocated)
        st.caption(f"Budget: {money(project['total_amount'], project['currency'])} · "
                   f"Allocated: {money(allocated, project['currency'])} · "
                   f"Remaining: {money(remaining, project['currency'])}")
        with st.form("add_milestone_form"):
            mtitle = st.text_input("Milestone title", placeholder="Homepage design")
            requirements = st.text_area(
                "Agreed requirements (be specific)",
                placeholder="1. Create homepage.\\n2. Include navigation bar.\\n3. Provide desktop and mobile layouts."
            )
            amount = st.number_input("Milestone amount", min_value=0.01, value=min(25.0, max(0.01, remaining)), step=5.0)
            due_date = st.date_input("Due date")
            add = st.form_submit_button("Add milestone", type="primary")
            if add:
                if not mtitle.strip() or not requirements.strip():
                    st.error("Enter a title and clear requirements.")
                elif float(amount) > remaining + 0.00001:
                    st.error("Milestone amount exceeds the remaining project budget.")
                else:
                    mid = add_milestone(project["id"], mtitle.strip(), requirements.strip(),
                                        float(amount), due_date.isoformat())
                    add_activity(project["id"], f"Milestone '{mtitle}' added.")
                    st.success(f"Milestone #{mid} added.")
                    st.rerun()

        st.subheader("Existing milestones")
        if existing:
            for m in existing:
                with st.expander(f"#{m['id']} · {m['title']} — {status_badge(m['status'])}"):
                    st.write(m["requirements"])
                    st.write(f"**Amount:** {money(m['amount'], project['currency'])}")
                    st.write(f"**Due:** {m['due_date'] or 'Not set'}")
        else:
            st.caption("No milestones have been added yet.")

# ---------- Submit work / AI ----------
elif page == "Submit Work & AI Review":
    st.subheader("Submit deliverable evidence")
    projects = list_projects()
    if not projects:
        st.info("Create a project and milestone first.")
    else:
        pmap = {f"#{p['id']} · {p['title']}": p for p in projects}
        plabel = st.selectbox("Project", list(pmap.keys()))
        project = pmap[plabel]
        milestones = list_milestones(project["id"])
        if not milestones:
            st.info("Add a milestone first.")
        else:
            mappable = {f"#{m['id']} · {m['title']} ({m['status']})": m for m in milestones}
            mlabel = st.selectbox("Milestone", list(mappable.keys()))
            milestone = mappable[mlabel]
            st.markdown("**Agreed requirements**")
            st.info(milestone["requirements"])
            if role != "Freelancer":
                st.warning("Switch the demo role to Freelancer to submit work.")
            else:
                with st.form("submission_form"):
                    evidence = st.text_area(
                        "Describe your completed work and evidence",
                        height=160,
                        placeholder="I completed the homepage and responsive mobile layout. The navigation menu is visible in the attached screenshots..."
                    )
                    uploaded = st.file_uploader("Optional evidence file (.txt or .md)", type=["txt", "md"])
                    submit_work = st.form_submit_button("Submit evidence and run AI review", type="primary")
                if submit_work:
                    if not evidence.strip() and uploaded is None:
                        st.error("Provide evidence text or upload a text file.")
                    else:
                        if uploaded:
                            file_text = uploaded.getvalue().decode("utf-8", errors="replace")
                            evidence = (evidence + "\n\nUploaded file content:\n" + file_text).strip()
                        sid = add_submission(milestone["id"], evidence)
                        with st.spinner("TrustPay AI is comparing evidence with the agreed requirements..."):
                            result = verify_milestone(milestone["requirements"], evidence)
                        save_verification(sid, result)
                        update_milestone_status(milestone["id"], "SUBMITTED")
                        add_activity(project["id"], f"Evidence submitted for '{milestone['title']}'.")
                        st.session_state["last_result"] = result
                        st.session_state["last_submission_id"] = sid
                        st.success("Evidence submitted and review completed.")
                        st.rerun()

            latest = list_submissions(milestone["id"])
            if latest:
                st.divider()
                st.markdown("**Previous submissions**")
                for sub in latest:
                    with st.expander(f"Submission #{sub['id']} · {sub['created_at']}"):
                        st.write(sub["evidence_text"])
                        v = get_latest_verification(sub["id"])
                        if v:
                            st.write(f"**Recommendation:** {v['recommendation']}")
                            st.write(f"**Confidence:** {float(v['confidence']):.0%}")
                            st.write(v["explanation"])
                            if v["completed_requirements"]:
                                st.write("**Supported requirements**")
                                for item in v["completed_requirements"]:
                                    st.write(f"✅ {item}")
                            if v["missing_requirements"]:
                                st.write("**Missing / unclear evidence**")
                                for item in v["missing_requirements"]:
                                    st.write(f"⚠️ {item}")

# ---------- Client approvals ----------
elif page == "Approvals":
    st.subheader("Client review and approval")
    if role != "Client":
        st.warning("Switch the demo role to Client to review submitted milestones.")
    projects = list_projects()
    pending = []
    for p in projects:
        for m in list_milestones(p["id"]):
            if m["status"] in ("SUBMITTED", "NEEDS_REVISION"):
                pending.append((p, m))
    if not pending:
        st.info("No milestones are currently awaiting client review.")
    for project, milestone in pending:
        with st.container(border=True):
            st.markdown(f"### {milestone['title']}")
            st.caption(f"Project: {project['title']} · Amount: {money(milestone['amount'], project['currency'])}")
            submissions = list_submissions(milestone["id"])
            if submissions:
                sub = submissions[0]
                st.write("**Freelancer's evidence**")
                st.write(sub["evidence_text"])
                v = get_latest_verification(sub["id"])
                if v:
                    st.write(f"**AI recommendation:** {v['recommendation']} · Confidence: {float(v['confidence']):.0%}")
                    st.info(v["explanation"])
                    for item in v["completed_requirements"]:
                        st.write(f"✅ {item}")
                    for item in v["missing_requirements"]:
                        st.write(f"⚠️ {item}")
            if role == "Client":
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Approve milestone", key=f"approve_{milestone['id']}", type="primary"):
                        update_milestone_status(milestone["id"], "APPROVED")
                        add_activity(project["id"], f"Client approved milestone '{milestone['title']}'.")
                        st.success("Milestone approved. Proceed to Payments to create PayPal checkout.")
                        st.rerun()
                with c2:
                    reason = st.text_input("Revision reason", key=f"reason_{milestone['id']}",
                                           placeholder="What needs to be changed?")
                    if st.button("Request revision", key=f"revise_{milestone['id']}"):
                        if not reason.strip():
                            st.error("Please provide a revision reason.")
                        else:
                            update_milestone_status(milestone["id"], "NEEDS_REVISION")
                            add_activity(project["id"], f"Revision requested for '{milestone['title']}': {reason}")
                            st.success("Revision requested.")
                            st.rerun()

# ---------- Payments ----------
elif page == "Payments":
    st.subheader("PayPal milestone payments")
    st.caption("Sandbox only. A client must approve a milestone before a PayPal order can be created.")
    service = paypal_service()
    configured = service.is_configured()
    if configured:
        st.success("PayPal credentials detected. Sandbox integration is configured.")
    else:
        st.warning("PayPal is not configured yet. You can test the rest of the app; follow the setup guide in About & Setup.")
    projects = list_projects()
    approved = []
    for p in projects:
        for m in list_milestones(p["id"]):
            if m["status"] == "APPROVED":
                approved.append((p, m))
    if approved:
        st.markdown("### Approved milestones ready for checkout")
        for p, m in approved:
            with st.container(border=True):
                st.write(f"**{p['title']} / {m['title']}**")
                st.write(money(m["amount"], p["currency"]))
                existing_payment = next((x for x in list_payments()
                                          if x["milestone_id"] == m["id"] and x["status"] != "FAILED"), None)
                if existing_payment:
                    st.info(f"A payment record already exists for this milestone (payment #{existing_payment['id']}). See Existing payment orders below.")
                elif role == "Client":
                    if st.button("Create PayPal checkout order", key=f"order_{m['id']}",
                                 disabled=not configured, type="primary"):
                        try:
                            with st.spinner("Creating PayPal order..."):
                                order = service.create_order(
                                    amount=m["amount"], currency=p["currency"],
                                    description=f"TrustPay milestone: {m['title']}",
                                    milestone_id=m["id"]
                                )
                            payment_id = create_payment_record(m["id"], order["id"], m["amount"], p["currency"])
                            update_payment_order(payment_id, order["id"], order.get("status", "CREATED"),
                                                 order.get("approval_url"))
                            add_activity(p["id"], f"PayPal order created for '{m['title']}'.")
                            st.session_state["created_order_id"] = order["id"]
                            st.success("PayPal order created.")
                            st.rerun()
                        except PayPalError as e:
                            st.error(str(e))
                else:
                    st.caption("Switch to Client role to create checkout.")
    else:
        st.info("No approved milestones are waiting for checkout.")

    st.divider()
    st.markdown("### Existing payment orders")
    payments = list_payments()
    if payments:
        for payment in payments:
            milestone = get_milestone(payment["milestone_id"])
            project = get_project(milestone["project_id"]) if milestone else None
            with st.container(border=True):
                st.write(f"**Payment #{payment['id']}** · {money(payment['amount'], payment['currency'])}")
                st.caption(f"Milestone: {milestone['title'] if milestone else 'Unknown'} · Status: {payment['status']}")
                if payment["paypal_order_id"]:
                    st.code(payment["paypal_order_id"])
                if payment["approval_url"]:
                    st.link_button("Open PayPal Sandbox Checkout", payment["approval_url"])
                if payment["status"] not in ("COMPLETED",) and payment["paypal_order_id"]:
                    if role == "Client":
                        if st.button("I approved checkout – capture payment", key=f"capture_{payment['id']}",
                                     type="primary"):
                            try:
                                with st.spinner("Capturing PayPal payment..."):
                                    capture = service.capture_order(payment["paypal_order_id"])
                                capture_id = service.extract_capture_id(capture)
                                update_payment_capture(payment["id"], capture_id, capture.get("status", "UNKNOWN"))
                                if capture.get("status") == "COMPLETED":
                                    update_milestone_status(payment["milestone_id"], "PAID")
                                    if project:
                                        add_activity(project["id"], f"PayPal payment captured for '{milestone['title']}'.")
                                    st.success("Payment captured successfully in PayPal Sandbox.")
                                else:
                                    st.warning(f"PayPal returned status: {capture.get('status')}")
                                st.rerun()
                            except PayPalError as e:
                                st.error(str(e))
                        st.caption("Only click after the buyer has completed PayPal approval in the checkout window.")
                    else:
                        st.caption("Switch to Client role to capture after buyer approval.")
    else:
        st.caption("No payment orders created yet.")


# ---------- About / setup ----------
elif page == "About & Setup":
    st.subheader("About TrustPay AI")
    st.write(
        "TrustPay AI helps freelancers and clients manage project milestones. "
        "Its AI reviews submitted evidence against agreed requirements and gives an advisory recommendation. "
        "The client remains responsible for approval, and PayPal handles the checkout and payment."
    )

    st.info(
        "This prototype is not an escrow service, does not hold customer funds, "
        "and does not provide a legal dispute decision."
    )

    st.subheader("Setup checklist")
    st.markdown("""
    1. Install dependencies from `requirements.txt`.
    2. Configure Ollama and download the selected local model.
    3. Set `TRUSTPAY_AI_PROVIDER=ollama` in `.env`.
    4. Configure PayPal Sandbox Client ID and Secret.
    5. Restart Streamlit after changing `.env`.
    """)

    st.subheader("AI mode")

    ai_provider = os.getenv("TRUSTPAY_AI_PROVIDER", "ollama").strip().lower()
    ai_model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    if ai_provider == "ollama":
        st.success(
            f"Local AI configured. Provider: Ollama | Model: {ai_model}"
        )
        st.caption(f"Ollama server: {ollama_url}")
        st.caption("No OpenAI API key is required for this configuration.")

    elif ai_provider == "demo":
        st.warning(
            "Demo heuristic mode is active. This is not an LLM-based review."
        )

    else:
        st.error(f"Unsupported AI provider: {ai_provider}")

    st.subheader("PayPal mode")

    if paypal_service().is_configured():
        st.success("PayPal Sandbox credentials are configured.")
    else:
        st.warning("PayPal Sandbox credentials are missing.")

    st.subheader("Important security notes")
    st.markdown("""
    - Use Sandbox credentials only while developing.
    - Never commit `.env` or API secrets to GitHub.
    - Demo role switching is not authentication or authorization.
    - Verify PayPal webhook signatures before using webhooks in production.
    - Do not claim funds are held in escrow.
    - Validate amounts and payment ownership on the server before capture.
    """)


st.caption("TrustPay AI · Hackathon prototype · Sandbox payments only")
