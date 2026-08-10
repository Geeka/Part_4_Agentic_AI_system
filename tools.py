
import os
import smtplib
from email.mime.text import MIMEText
import serpapi

# ---------- job search call using SERPAPI ----------
def call_api(query: str, num_results: int = 10) -> list:
    """Calls SerpApi Google Jobs directly, filtered to postings from the last 7 days."""
    client = serpapi.Client(api_key=os.environ.get("SERPAPI_API_KEY"))
    results = client.search({
        "engine": "google_jobs",
        "q": query,
        "hl": "en",
        "chips": "date_posted:week",
    })
    jobs_results = results.get("jobs_results", [])

    return jobs_results[:num_results]


# ---------- pull clean fields out of a raw job result ----------
def extract_job_fields(raw_result: dict) -> dict:
    apply_options = raw_result.get("apply_options") or [{}]
    description = raw_result.get("description", "").replace("\r\n", " ").strip()
    return {
        "title": raw_result.get("title", ""),
        "company": raw_result.get("company_name", ""),
        "location": raw_result.get("location", "Not listed"),
        "description": description[:1500],  # capped -- guards against any oversized/garbled field
        # Only apply_options (the actual employer/job-board apply page) is
        # used. share_link is Google's own redirect/search page, not a
        # real apply page -- left blank rather than falling back to it.
        "apply_link": apply_options[0].get("link", ""),
    }

def render_email_body(email_data: dict) -> str:
    """Fixed template every run -- only content varies, never structure or wording.
    Called only from process_final_output, never by any agent."""
    jobs = email_data.get("jobs", [])
    top_pick = email_data.get("top_pick", {})
    why = email_data.get("why_this_one", "")

    lines = ["Hi,", "", "Here are the latest job matches found for you this week.", ""]

    if top_pick:
        lines += [
            "=" * 50, "TOP PICK", "=" * 50,
            f"{top_pick.get('title', '(no title)')} at {top_pick.get('company', '(unknown company)')}",
            f"Location: {top_pick.get('location', '(not specified)')}",
        ]
        if why:
            lines.append(f"\nWhy this one: {why}")
        if top_pick.get("apply_link"):
            lines.append(f"\nApply here: {top_pick['apply_link']}")
        lines.append("")

    lines += ["=" * 50, f"ALL {len(jobs)} JOBS FOUND", "=" * 50]
    for i, job in enumerate(jobs, start=1):
        desc = job.get("description", "")
        short_desc = (desc[:280] + "...") if len(desc) > 280 else desc
        lines += [
            f"\n{i}. {job.get('title', '(no title)')} -- {job.get('company', '(unknown company)')}",
            f"   Location: {job.get('location', '(not specified)')}",
        ]
        if short_desc:
            lines.append(f"   {short_desc}")
        if job.get("apply_link"):
            lines.append(f"   Apply: {job['apply_link']}")

    lines += ["", "", "Good luck with your applications!"]
    return "\n".join(lines)

# ---------- plain SMTP send, no agent involved ----------
def send_email(to_email: str, subject: str, body: str) -> str:
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    message = MIMEText(body, "html")
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [to_email], message.as_string())
        return f"Email successfully sent to {to_email}"
    except Exception as e:
        return f"Error sending email: {e}"

