import os
import re
import json
import html
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)


# =========================
# SETUP
# =========================
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

TARGET_CV_SCORE = 80
MAX_CV_REWRITE_ATTEMPTS = 3

st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="🚀",
    layout="wide"
)


# =========================
# CSS
# =========================
st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(circle at 10% 10%, rgba(255, 45, 149, 0.32), transparent 28%),
            radial-gradient(circle at 90% 10%, rgba(0, 229, 255, 0.34), transparent 28%),
            radial-gradient(circle at 20% 90%, rgba(255, 193, 7, 0.26), transparent 30%),
            radial-gradient(circle at 85% 85%, rgba(0, 255, 150, 0.25), transparent 30%),
            linear-gradient(135deg, #07111f 0%, #101a35 45%, #160d2e 100%);
        color: #ffffff;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.22), rgba(255,255,255,0.08));
        border: 1px solid rgba(255,255,255,0.24);
        border-radius: 32px;
        padding: 34px;
        box-shadow:
            0 28px 70px rgba(0,0,0,0.35),
            inset 0 1px 0 rgba(255,255,255,0.20);
        backdrop-filter: blur(20px);
        margin-bottom: 24px;
    }

    .hero-title {
        font-size: 2.65rem;
        font-weight: 900;
        color: #ffffff;
        text-shadow: 0 8px 24px rgba(0,0,0,0.35);
        margin-bottom: 10px;
    }

    .hero-subtitle {
        color: #e8f3ff;
        font-size: 1.05rem;
        line-height: 1.8;
    }

    .rainbow-line {
        height: 5px;
        width: 280px;
        border-radius: 999px;
        background: linear-gradient(90deg, #ff2d95, #00e5ff, #00ff96, #ffcc00);
        margin-top: 18px;
        box-shadow: 0 10px 30px rgba(0,229,255,0.35);
    }

    .glass-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.17), rgba(255,255,255,0.07));
        border: 1px solid rgba(255,255,255,0.20);
        border-radius: 26px;
        padding: 22px;
        box-shadow:
            0 20px 50px rgba(0,0,0,0.28),
            inset 0 1px 0 rgba(255,255,255,0.16);
        backdrop-filter: blur(18px);
        margin-bottom: 20px;
    }

    .card-title {
        font-size: 1.2rem;
        font-weight: 850;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .card-text {
        color: #dcecff;
        font-size: 0.95rem;
        line-height: 1.7;
    }

    .status-card {
        background: linear-gradient(135deg, rgba(0,255,150,0.18), rgba(0,229,255,0.13));
        border: 1px solid rgba(0,255,150,0.32);
        border-radius: 20px;
        padding: 16px;
        color: #eafff6;
        font-weight: 700;
        margin-bottom: 16px;
        box-shadow: 0 16px 35px rgba(0,0,0,0.22);
    }

    .warning-card {
        background: linear-gradient(135deg, rgba(255,193,7,0.16), rgba(255,45,149,0.12));
        border: 1px solid rgba(255,193,7,0.34);
        border-radius: 20px;
        padding: 16px;
        color: #fff6d7;
        line-height: 1.65;
        margin-bottom: 18px;
    }

    .feature-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 8px 13px;
        margin: 5px 6px 5px 0;
        color: white;
        font-weight: 700;
        font-size: 0.88rem;
        border: 1px solid rgba(255,255,255,0.20);
        background: linear-gradient(135deg, rgba(255,45,149,0.30), rgba(0,229,255,0.25));
    }

    .tag-good {
        display: inline-block;
        border-radius: 999px;
        padding: 8px 13px;
        margin: 5px 6px 5px 0;
        color: #ffffff;
        font-weight: 700;
        font-size: 0.87rem;
        background: linear-gradient(135deg, rgba(0,255,150,0.28), rgba(0,229,255,0.20));
        border: 1px solid rgba(0,255,150,0.28);
    }

    .tag-missing {
        display: inline-block;
        border-radius: 999px;
        padding: 8px 13px;
        margin: 5px 6px 5px 0;
        color: #ffffff;
        font-weight: 700;
        font-size: 0.87rem;
        background: linear-gradient(135deg, rgba(255,193,7,0.30), rgba(255,45,149,0.22));
        border: 1px solid rgba(255,193,7,0.28);
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(255,255,255,0.18), rgba(255,255,255,0.07));
        border: 1px solid rgba(255,255,255,0.20);
        border-radius: 24px;
        padding: 18px;
        box-shadow:
            0 18px 40px rgba(0,0,0,0.25),
            inset 0 1px 0 rgba(255,255,255,0.15);
    }

    div[data-testid="stMetric"] label {
        color: #e6f3ff !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetric"] div {
        color: #ffffff !important;
    }

    div[data-testid="stWidgetLabel"] p {
        color: #e8f3ff !important;
        font-weight: 700 !important;
    }

    .stTextArea textarea,
    .stTextInput input {
        background: #F8FAFC !important;
        color: #111827 !important;
        border-radius: 18px !important;
        border: 1px solid rgba(255,255,255,0.22) !important;
    }

    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder {
        color: #64748B !important;
    }

    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: #F8FAFC !important;
        color: #111827 !important;
        border-radius: 18px !important;
        border: 1px solid rgba(255,255,255,0.22) !important;
    }

    .stSelectbox span,
    .stMultiSelect span {
        color: #111827 !important;
    }

    .stFileUploader {
        background: linear-gradient(145deg, rgba(255,255,255,0.14), rgba(255,255,255,0.06));
        border-radius: 20px;
        padding: 12px;
        border: 1px dashed rgba(255,255,255,0.28);
    }

    div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.08) !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
    }

    div[data-testid="stExpander"] summary p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    .stButton button {
        width: 100%;
        border-radius: 20px;
        border: none;
        padding: 0.95rem 1rem;
        color: white;
        font-weight: 900;
        font-size: 1.05rem;
        background: linear-gradient(135deg, #ff2d95, #7b61ff, #00e5ff, #00ff96);
        box-shadow: 0 18px 42px rgba(0,229,255,0.30);
        transition: all 0.25s ease;
    }

    .stButton button:hover {
        transform: translateY(-3px) scale(1.01);
        box-shadow: 0 24px 52px rgba(255,45,149,0.32);
    }

    .stDownloadButton button {
        border-radius: 16px;
        font-weight: 850;
        background: linear-gradient(135deg, #00e5ff, #7b61ff, #ff2d95) !important;
        color: white !important;
        border: none !important;
    }

    .result-panel {
        background: linear-gradient(145deg, rgba(255,255,255,0.15), rgba(255,255,255,0.06));
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 26px;
        padding: 24px;
        box-shadow:
            0 18px 45px rgba(0,0,0,0.25),
            inset 0 1px 0 rgba(255,255,255,0.14);
        margin-top: 12px;
    }

    .footer {
        color: #c7dcff;
        font-size: 0.9rem;
        line-height: 1.7;
        margin-top: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# FILE READING FUNCTIONS
# =========================
def read_pdf(uploaded_file):
    text = ""
    reader = PdfReader(uploaded_file)

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text.strip()


def read_docx(uploaded_file):
    document = Document(uploaded_file)
    text = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text.append(paragraph.text)

    return "\n".join(text).strip()


def read_txt(uploaded_file):
    return uploaded_file.getvalue().decode("utf-8", errors="ignore").strip()


def read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    try:
        if file_name.endswith(".pdf"):
            return read_pdf(uploaded_file)
        elif file_name.endswith(".docx"):
            return read_docx(uploaded_file)
        elif file_name.endswith(".txt"):
            return read_txt(uploaded_file)
        else:
            return ""
    except Exception as error:
        st.error(f"Could not read {uploaded_file.name}. Error: {error}")
        return ""


# =========================
# SCORING FUNCTIONS
# =========================
def normalise_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_keywords(text, limit=45):
    text_lower = normalise_text(text)

    phrase_patterns = [
        "customer service", "technical support", "service desk", "help desk",
        "stakeholder management", "incident management", "problem management",
        "change management", "microsoft 365", "office 365", "active directory",
        "azure active directory", "entra id", "intune", "exchange online",
        "sharepoint", "onedrive", "teams", "defender", "cyber security",
        "information security", "network troubleshooting", "system administration",
        "windows 10", "windows 11", "windows server", "powershell", "vpn",
        "mfa", "conditional access", "autopilot", "endpoint management",
        "cloud computing", "azure", "aws", "amazon web services", "google cloud",
        "power bi", "sql", "python", "data analysis", "business analysis",
        "project management", "documentation", "reporting", "compliance",
        "risk management", "communication skills", "time management",
        "leadership", "team collaboration", "customer success", "troubleshooting",
        "ticketing system", "jira", "servicenow", "itil", "network support",
        "network administration", "desktop support", "hardware troubleshooting",
        "software troubleshooting", "user support", "endpoint security",
        "routers", "switches", "firewalls", "dns", "dhcp", "tcp/ip",
        "lan", "wan", "wi-fi", "wireless", "printer support"
    ]

    found_phrases = [phrase for phrase in phrase_patterns if phrase in text_lower]

    stopwords = {
        "the", "and", "for", "that", "with", "this", "from", "will", "your", "have",
        "has", "our", "you", "are", "but", "not", "all", "can", "their", "they",
        "who", "was", "were", "been", "being", "job", "role", "work", "want",
        "must", "should", "would", "about", "into", "more", "than", "then",
        "there", "here", "very", "such", "using", "used", "need", "needs",
        "high", "well", "good", "able", "strong", "including", "within", "across",
        "each", "other", "some", "most", "any", "one", "two", "three", "new",
        "also", "after", "before", "under", "over", "through", "make", "made",
        "like", "when", "where", "which", "while", "because", "based", "support",
        "experience", "skills", "skill", "candidate", "position", "resume",
        "description", "application", "company", "team", "business", "provide"
    }

    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#/\-]{2,}", text_lower)

    frequency = {}

    for token in tokens:
        if token not in stopwords and len(token) > 2:
            frequency[token] = frequency.get(token, 0) + 1

    ranked_tokens = [
        token for token, count in sorted(
            frequency.items(),
            key=lambda item: (-item[1], item[0])
        )
    ]

    combined = []

    for item in found_phrases + ranked_tokens:
        if item not in combined:
            combined.append(item)

    return combined[:limit]


def score_band(score):
    if score >= 85:
        return "Excellent Match"
    elif score >= 80:
        return "Target Score Reached"
    elif score >= 72:
        return "Strong Match"
    elif score >= 58:
        return "Moderate Match"
    elif score >= 45:
        return "Possible Match"
    else:
        return "Needs Major Improvement"


def calculate_score(resume, job_description, work_rights, target_location):
    resume_text = normalise_text(resume)

    jd_keywords = extract_keywords(job_description, limit=40)
    matched_keywords = [keyword for keyword in jd_keywords if keyword in resume_text]
    missing_keywords = [keyword for keyword in jd_keywords if keyword not in resume_text]

    keyword_ratio = len(matched_keywords) / max(1, len(jd_keywords))
    keyword_score = min(45, round(keyword_ratio * 45))

    section_checks = {
        "summary/profile": any(x in resume_text for x in [
            "summary", "profile", "professional summary",
            "career summary", "professional profile"
        ]),
        "experience": any(x in resume_text for x in [
            "experience", "employment", "work history", "professional experience"
        ]),
        "education": "education" in resume_text,
        "skills": "skills" in resume_text,
        "certifications/projects": any(x in resume_text for x in [
            "certification", "certifications", "projects", "project"
        ])
    }

    structure_score = sum(3 for value in section_checks.values() if value)

    number_hits = len(re.findall(r"\b\d+%|\$\d[\d,]*|\b\d+\+?\b", resume))
    action_hits = len(re.findall(
        r"\b(led|managed|implemented|delivered|reduced|increased|improved|supported|resolved|designed|built|migrated|automated|configured|deployed|trained|documented|maintained|assisted|monitored|installed|administered|coordinated|troubleshot|upgraded|diagnosed|escalated)\b",
        resume_text
    ))

    achievement_score = min(10, round((min(number_hits, 8) + min(action_hits, 8)) / 16 * 10))

    ats_score = 0

    if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume):
        ats_score += 3

    if re.search(r"(\+?\d[\d\s\-]{7,}\d)", resume):
        ats_score += 3

    if "linkedin.com" in resume_text or "linkedin" in resume_text:
        ats_score += 2

    if len(re.findall(r"•|-|\*", resume)) >= 5:
        ats_score += 3

    word_count = len(resume.split())

    if 300 <= word_count <= 1500:
        ats_score += 4
    elif 220 <= word_count < 300 or 1500 < word_count <= 1800:
        ats_score += 2

    ats_score = min(15, ats_score)

    au_score = 0

    australia_signals = [
        "australia", "australian", "working rights", "work rights",
        "full working rights", "permanent resident", "citizen", "visa",
        "brisbane", "gold coast", "sydney", "melbourne", "perth", "adelaide",
        "canberra", "queensland", "nsw", "victoria", "wa", "sa",
        "driver licence", "drivers licence", "police check", "blue card",
        "wwcc", "ndis", "local experience"
    ]

    au_hits = sum(1 for signal in australia_signals if signal in resume_text)
    au_score += min(8, au_hits)

    if work_rights != "Prefer not to say":
        au_score += 5

    if target_location != "Australia-wide" and target_location.lower() in resume_text:
        au_score += 2
    elif keyword_ratio >= 0.45:
        au_score += 2

    au_score = min(15, au_score)

    total_score = keyword_score + structure_score + achievement_score + ats_score + au_score
    total_score = max(0, min(100, total_score))

    return {
        "total_score": total_score,
        "band": score_band(total_score),
        "keyword_score": keyword_score,
        "structure_score": structure_score,
        "achievement_score": achievement_score,
        "ats_score": ats_score,
        "au_score": au_score,
        "matched_keywords": matched_keywords[:20],
        "missing_keywords": missing_keywords[:20],
        "jd_keywords_count": len(jd_keywords),
        "matched_count": len(matched_keywords),
        "keyword_match_percent": round(keyword_ratio * 100)
    }


def render_tags(items, tag_class):
    if not items:
        return f"<span class='{tag_class}'>None identified</span>"

    return "".join([f"<span class='{tag_class}'>{item}</span>" for item in items])


# =========================
# OPENAI FUNCTIONS
# =========================
def ask_ai(prompt):
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=(
            "You are a senior Australian career coach, recruiter advisor, resume writer, and ATS specialist. "
            "Write in Australian English. Give honest and practical advice based on the Australian job market. "
            "Do not invent experience, employers, qualifications, certifications, dates, work rights, or achievements. "
            "Do not recommend adding photo, date of birth, religion, marital status, or sensitive personal details. "
            "Focus on ATS, quantified achievements, keywords, work rights clarity, local experience, communication, and recruiter expectations in Australia."
        ),
        input=prompt
    )

    return response.output_text


def extract_json_from_text(text):
    cleaned = text.strip()

    cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^```", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI did not return a valid JSON object.")

    cleaned = cleaned[start:end + 1]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        pass

    cleaned_fixed = re.sub(r"[\x00-\x1F\x7F]", " ", cleaned)
    cleaned_fixed = re.sub(r",\s*}", "}", cleaned_fixed)
    cleaned_fixed = re.sub(r",\s*]", "]", cleaned_fixed)

    try:
        return json.loads(cleaned_fixed, strict=False)
    except json.JSONDecodeError as error:
        preview = cleaned_fixed[:700]
        raise ValueError(
            f"Could not parse AI JSON output. Error: {error}. Preview: {preview}"
        )


def generate_optimised_cv_json(base_context, score_feedback=""):
    cv_prompt = f"""
{base_context}

Score improvement target:
Try to produce an updated CV that can reach at least {TARGET_CV_SCORE}/100 using the app's scoring criteria.

Current improvement feedback:
{score_feedback}

Rewrite the resume into a polished, ready-to-submit Australian-style CV tailored to the job description.

Important rules:
- Do not invent experience.
- Do not invent employers.
- Do not invent certifications.
- Do not invent dates.
- Do not invent work rights.
- Do not invent degrees.
- Do not invent fake numbers.
- Use only information clearly supported by the original resume.
- You may rewrite, reorder, strengthen, and tailor wording.
- Include relevant job-description keywords naturally inside the profile, skills, technical skills, and experience bullets only where truthful.
- Do not create a separate "Relevant Keywords" section.
- Improve ATS keyword alignment naturally.
- Improve professional profile.
- Improve key skills.
- Improve technical skills.
- Improve achievement-focused bullet points.
- Use action verbs such as supported, resolved, configured, managed, implemented, documented, improved, assisted, maintained, monitored, installed, administered, coordinated, diagnosed, escalated and troubleshot where truthful.
- Make sure the CV has these sections: Professional Profile, Key Skills, Technical Skills, Professional Experience, Education, Projects or Certifications if supported.
- Use Australian English.
- Make the CV suitable for Australian recruiters.
- Avoid photos, graphics, date of birth, marital status, religion, and unnecessary personal details.
- If exact numbers are not in the original resume, do not create new numbers.
- If name/contact details are missing, leave those fields blank.

JSON rules:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanation.
- Do not use comments.
- Do not use trailing commas.
- Escape all new lines inside string values.
- Use double quotes only.

Return this exact JSON structure:

{{
  "name": "",
  "target_title": "",
  "contact": {{
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": ""
  }},
  "profile": "",
  "key_skills": [],
  "technical_skills": [
    {{
      "category": "",
      "items": []
    }}
  ],
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "location": "",
      "dates": "",
      "summary": "",
      "achievements": []
    }}
  ],
  "projects": [
    {{
      "title": "",
      "details": []
    }}
  ],
  "education": [
    {{
      "qualification": "",
      "institution": "",
      "dates": ""
    }}
  ],
  "certifications": [],
  "additional_information": []
}}

If a field is unknown, use an empty string or empty list.
"""

    last_error = None

    for retry in range(1, 4):
        response_text = ask_ai(cv_prompt)

        try:
            return extract_json_from_text(response_text)
        except Exception as error:
            last_error = error

            cv_prompt = f"""
The previous response was invalid JSON.

Error:
{error}

Fix the issue and return ONLY valid JSON.

Rules:
- No markdown.
- No explanation.
- No code fence.
- No raw line breaks inside string values.
- Escape new lines as \\n if needed.
- Use double quotes.
- No trailing commas.
- Do not invent experience, employers, dates, certificates, work rights, or numbers.
- Do not create a separate "Relevant Keywords" section.

Use the same JSON structure as requested earlier.

Context:
{base_context}

Score feedback:
{score_feedback}
"""

    raise ValueError(f"AI failed to return valid JSON after 3 attempts. Last error: {last_error}")


# =========================
# PDF FUNCTIONS
# =========================
def safe_text(value):
    if value is None:
        return ""
    return html.escape(str(value)).replace("\n", "<br/>")


def cv_json_to_plain_text(cv_data):
    parts = []

    contact = cv_data.get("contact", {})

    parts.append(cv_data.get("name", ""))
    parts.append(cv_data.get("target_title", ""))

    parts.append(contact.get("email", ""))
    parts.append(contact.get("phone", ""))
    parts.append(contact.get("location", ""))
    parts.append(contact.get("linkedin", ""))

    parts.append("Professional Profile")
    parts.append(cv_data.get("profile", ""))

    parts.append("Skills")
    parts.append("Key Skills")
    for item in cv_data.get("key_skills", []):
        parts.append(item)

    parts.append("Technical Skills")
    for category in cv_data.get("technical_skills", []):
        parts.append(category.get("category", ""))
        parts.extend(category.get("items", []))

    parts.append("Professional Experience")
    parts.append("Experience")
    for job in cv_data.get("experience", []):
        parts.append(job.get("job_title", ""))
        parts.append(job.get("company", ""))
        parts.append(job.get("location", ""))
        parts.append(job.get("dates", ""))
        parts.append(job.get("summary", ""))

        for achievement in job.get("achievements", []):
            parts.append(f"- {achievement}")

    parts.append("Projects")
    for project in cv_data.get("projects", []):
        parts.append(project.get("title", ""))

        for detail in project.get("details", []):
            parts.append(f"- {detail}")

    parts.append("Education")
    for education in cv_data.get("education", []):
        parts.append(education.get("qualification", ""))
        parts.append(education.get("institution", ""))
        parts.append(education.get("dates", ""))

    parts.append("Certifications")
    for cert in cv_data.get("certifications", []):
        parts.append(f"- {cert}")

    parts.append("Additional Information")
    for info in cv_data.get("additional_information", []):
        parts.append(f"- {info}")

    return "\n".join([str(p) for p in parts if str(p).strip()])


def create_optimised_cv_pdf(cv_data, target_role):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm
    )

    base_styles = getSampleStyleSheet()

    styles = {
        "Name": ParagraphStyle(
            "Name",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#FFFFFF"),
            alignment=TA_LEFT,
            spaceAfter=3
        ),
        "Target": ParagraphStyle(
            "Target",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#D7E7FF"),
            alignment=TA_LEFT,
            spaceAfter=5
        ),
        "Contact": ParagraphStyle(
            "Contact",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=11,
            textColor=colors.HexColor("#F1F5F9"),
            alignment=TA_LEFT
        ),
        "SectionTitle": ParagraphStyle(
            "SectionTitle",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=5
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=12.8,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=4
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.6,
            leading=11.5,
            textColor=colors.HexColor("#475569"),
            spaceAfter=3
        ),
        "JobTitle": ParagraphStyle(
            "JobTitle",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=2
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=12.2,
            textColor=colors.HexColor("#1F2937"),
            leftIndent=12,
            firstLineIndent=0,
            bulletIndent=4,
            spaceAfter=2.5
        )
    }

    story = []

    name = cv_data.get("name", "").strip() or "Candidate Name"
    title = cv_data.get("target_title", "").strip() or target_role or "Target Role"

    contact = cv_data.get("contact", {})
    contact_parts = [
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("location", ""),
        contact.get("linkedin", "")
    ]

    contact_line = " | ".join([str(part).strip() for part in contact_parts if str(part).strip()])

    header_rows = [
        [Paragraph(safe_text(name), styles["Name"])],
        [Paragraph(safe_text(title), styles["Target"])]
    ]

    if contact_line:
        header_rows.append([Paragraph(safe_text(contact_line), styles["Contact"])])

    header_table = Table(
        header_rows,
        colWidths=[178 * mm]
    )

    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
        ("BOX", (0, 0), (-1, -1), 0, colors.HexColor("#0F172A")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (0, 0), 12),
        ("BOTTOMPADDING", (0, -1), (0, -1), 12),
    ]))

    story.append(header_table)

    accent_bar = Table(
        [["", "", ""]],
        colWidths=[59.3 * mm, 59.3 * mm, 59.3 * mm],
        rowHeights=[2.5 * mm]
    )

    accent_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#2563EB")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#06B6D4")),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#22C55E")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(accent_bar)
    story.append(Spacer(1, 8))

    def section_title(title_text):
        story.append(Spacer(1, 5))

        section_table = Table(
            [[Paragraph(safe_text(title_text.upper()), styles["SectionTitle"])]],
            colWidths=[178 * mm]
        )

        section_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF6FF")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.7, colors.HexColor("#2563EB")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        story.append(section_table)
        story.append(Spacer(1, 5))

    def bullet_list(items):
        for item in items:
            if str(item).strip():
                story.append(
                    Paragraph(
                        safe_text(item),
                        styles["Bullet"],
                        bulletText="-"
                    )
                )

    profile = cv_data.get("profile", "").strip()

    if profile:
        section_title("Professional Profile")
        story.append(Paragraph(safe_text(profile), styles["Body"]))

    key_skills = cv_data.get("key_skills", [])

    if key_skills:
        section_title("Key Skills")

        clean_skills = [str(skill).strip() for skill in key_skills if str(skill).strip()]
        skill_rows = []

        for i in range(0, len(clean_skills), 3):
            row = clean_skills[i:i + 3]
            while len(row) < 3:
                row.append("")
            skill_rows.append([Paragraph(safe_text(skill), styles["Small"]) for skill in row])

        skills_table = Table(
            skill_rows,
            colWidths=[58.5 * mm, 58.5 * mm, 58.5 * mm]
        )

        skills_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        story.append(skills_table)

    technical_skills = cv_data.get("technical_skills", [])

    if technical_skills:
        section_title("Technical Skills")

        for skill_group in technical_skills:
            category = skill_group.get("category", "")
            items = skill_group.get("items", [])

            if category or items:
                items_text = ", ".join([str(item).strip() for item in items if str(item).strip()])
                line = f"<b>{safe_text(category)}:</b> {safe_text(items_text)}"
                story.append(Paragraph(line, styles["Body"]))

    experience = cv_data.get("experience", [])

    if experience:
        section_title("Professional Experience")

        for job in experience:
            job_title = job.get("job_title", "")
            company = job.get("company", "")
            location = job.get("location", "")
            dates = job.get("dates", "")
            summary = job.get("summary", "")
            achievements = job.get("achievements", [])

            heading_parts = [part for part in [job_title, company] if str(part).strip()]
            heading = " | ".join(heading_parts)

            meta_parts = [part for part in [location, dates] if str(part).strip()]
            meta_line = " | ".join(meta_parts)

            job_block = []

            if heading:
                job_block.append(Paragraph(safe_text(heading), styles["JobTitle"]))

            if meta_line:
                job_block.append(Paragraph(safe_text(meta_line), styles["Small"]))

            if summary:
                job_block.append(Paragraph(safe_text(summary), styles["Body"]))

            for achievement in achievements:
                if str(achievement).strip():
                    job_block.append(
                        Paragraph(
                            safe_text(achievement),
                            styles["Bullet"],
                            bulletText="-"
                        )
                    )

            story.append(KeepTogether(job_block))
            story.append(Spacer(1, 5))

    projects = cv_data.get("projects", [])

    if projects:
        section_title("Projects")

        for project in projects:
            project_title = project.get("title", "")
            details = project.get("details", [])

            if project_title:
                story.append(Paragraph(safe_text(project_title), styles["JobTitle"]))

            bullet_list(details)

    education = cv_data.get("education", [])

    if education:
        section_title("Education")

        for item in education:
            qualification = item.get("qualification", "")
            institution = item.get("institution", "")
            dates = item.get("dates", "")

            line_parts = [part for part in [qualification, institution, dates] if str(part).strip()]

            if line_parts:
                story.append(Paragraph(safe_text(" | ".join(line_parts)), styles["Body"]))

    certifications = cv_data.get("certifications", [])

    if certifications:
        section_title("Certifications")
        bullet_list(certifications)

    additional_information = cv_data.get("additional_information", [])

    if additional_information:
        section_title("Additional Information")
        bullet_list(additional_information)

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


# =========================
# API CHECK
# =========================
if not api_key:
    st.error("OPENAI_API_KEY is missing. Please add it to your .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

if "results" not in st.session_state:
    st.session_state.results = None


# =========================
# HERO
# =========================
st.markdown(f"""
<div class="hero-card">
    <div class="hero-title">🚀 AI Job Application Assistant</div>
    <div class="hero-subtitle">
        Attach your resume and job description. The app analyses your match score, gives Australian job market advice,
        and generates a polished, ready-to-submit CV in PDF format. The app will try to reach an updated CV score of
        <b>{TARGET_CV_SCORE}/100</b> without creating fake experience.
    </div>
    <div class="rainbow-line"></div>
    <br>
    <span class="feature-pill">Private File Attach</span>
    <span class="feature-pill">No Text Preview</span>
    <span class="feature-pill">ATS Score</span>
    <span class="feature-pill">Target 80/100</span>
    <span class="feature-pill">Australian CV PDF</span>
    <span class="feature-pill">Cover Letter</span>
</div>
""", unsafe_allow_html=True)


# =========================
# INPUT LAYOUT
# =========================
left_col, right_col = st.columns([1.7, 1], gap="large")

with left_col:
    st.markdown("""
    <div class="glass-card">
        <div class="card-title">📎 Attach Resume</div>
        <div class="card-text">
            Upload your resume as PDF, DOCX, or TXT. The file will be used for calculation only.
            The extracted text will not be displayed.
        </div>
    </div>
    """, unsafe_allow_html=True)

    resume_file = st.file_uploader(
        "Attach Resume File",
        type=["pdf", "docx", "txt"],
        key="resume_upload"
    )

    uploaded_resume_text = read_uploaded_file(resume_file)

    if resume_file:
        if uploaded_resume_text:
            st.markdown(
                f"<div class='status-card'>✅ Resume attached successfully: {resume_file.name}</div>",
                unsafe_allow_html=True
            )
        else:
            st.error("Resume was attached, but no readable text was found. Try another PDF, DOCX, or TXT file.")

    with st.expander("Or paste resume manually"):
        manual_resume_text = st.text_area(
            "Paste Resume Text",
            height=220,
            placeholder="Paste your resume here only if you do not want to upload a file..."
        )

    st.markdown("""
    <div class="glass-card">
        <div class="card-title">📎 Attach Job Description</div>
        <div class="card-text">
            Upload the job description as PDF, DOCX, or TXT. The extracted text will not be displayed.
        </div>
    </div>
    """, unsafe_allow_html=True)

    jd_file = st.file_uploader(
        "Attach Job Description File",
        type=["pdf", "docx", "txt"],
        key="jd_upload"
    )

    uploaded_jd_text = read_uploaded_file(jd_file)

    if jd_file:
        if uploaded_jd_text:
            st.markdown(
                f"<div class='status-card'>✅ Job description attached successfully: {jd_file.name}</div>",
                unsafe_allow_html=True
            )
        else:
            st.error("Job description was attached, but no readable text was found. Try another PDF, DOCX, or TXT file.")

    with st.expander("Or paste job description manually"):
        manual_jd_text = st.text_area(
            "Paste Job Description Text",
            height=220,
            placeholder="Paste the job description here only if you do not want to upload a file..."
        )

    final_resume_text = uploaded_resume_text if uploaded_resume_text else manual_resume_text
    final_jd_text = uploaded_jd_text if uploaded_jd_text else manual_jd_text

with right_col:
    st.markdown("""
    <div class="glass-card">
        <div class="card-title">⚙️ Application Settings</div>
        <div class="card-text">
            These options help the AI tailor the CV and advice to your target role.
        </div>
    </div>
    """, unsafe_allow_html=True)

    target_role = st.text_input(
        "Target Role",
        placeholder="Example: Network Support Analyst, ICT Support Officer"
    )

    target_location = st.selectbox(
        "Target Location",
        [
            "Australia-wide",
            "Brisbane",
            "Gold Coast",
            "Sydney",
            "Melbourne",
            "Perth",
            "Adelaide",
            "Canberra",
            "Regional Australia"
        ]
    )

    work_rights = st.selectbox(
        "Work Rights / Visa Status",
        [
            "Prefer not to say",
            "Australian Citizen",
            "Permanent Resident",
            "Full Working Rights",
            "Temporary Graduate Visa 485",
            "Student Visa",
            "Requires Sponsorship"
        ]
    )

    career_level = st.selectbox(
        "Career Level",
        [
            "Entry Level",
            "Junior",
            "Mid Level",
            "Senior",
            "Manager"
        ]
    )

    cover_letter_tone = st.selectbox(
        "Cover Letter Tone",
        [
            "Professional",
            "Confident",
            "Friendly",
            "Formal",
            "Short and Direct"
        ]
    )

    st.markdown(f"""
    <div class="warning-card">
        <b>Target:</b> The app will attempt up to {MAX_CV_REWRITE_ATTEMPTS} CV rewrites to reach {TARGET_CV_SCORE}/100.
        It will not create fake experience, employers, dates, certifications, numbers, or work rights.
    </div>
    """, unsafe_allow_html=True)

    analyse_button = st.button("✨ Analyse & Generate Ready CV PDF")


# =========================
# ANALYSIS PROCESS
# =========================
if analyse_button:
    if not final_resume_text.strip() or not final_jd_text.strip():
        st.warning("Please attach or paste both your resume and the job description.")
    else:
        with st.spinner(f"Analysing your files and trying to reach {TARGET_CV_SCORE}/100..."):
            original_score_data = calculate_score(
                resume=final_resume_text,
                job_description=final_jd_text,
                work_rights=work_rights,
                target_location=target_location
            )

            matched_keywords_text = ", ".join(original_score_data["matched_keywords"]) if original_score_data["matched_keywords"] else "None"
            missing_keywords_text = ", ".join(original_score_data["missing_keywords"]) if original_score_data["missing_keywords"] else "None"

            base_context = f"""
Target role: {target_role if target_role.strip() else "Not specified"}
Target location: {target_location}
Work rights / visa status: {work_rights}
Career level: {career_level}

Original calculated score:
- Overall score: {original_score_data["total_score"]}/100
- Score band: {original_score_data["band"]}
- Keyword alignment: {original_score_data["keyword_score"]}/45
- Resume structure: {original_score_data["structure_score"]}/15
- Achievement evidence: {original_score_data["achievement_score"]}/10
- ATS quality: {original_score_data["ats_score"]}/15
- Australian market readiness: {original_score_data["au_score"]}/15
- Keyword match percentage: {original_score_data["keyword_match_percent"]}%

Matched keywords:
{matched_keywords_text}

Missing or weak keywords:
{missing_keywords_text}

Original Resume:
{final_resume_text}

Job Description:
{final_jd_text}
"""

            analysis_prompt = f"""
{base_context}

Create a detailed resume and job application analysis in markdown.

Use this exact structure:

## 1. Honest Match Assessment
Give a direct and realistic assessment of the candidate's suitability.

## 2. Match Score Explanation
Explain why the score is high, medium, or low based on the score breakdown.

## 3. Strongest Selling Points
List the strongest points in the resume.

## 4. Weak Areas Holding the Candidate Back
Explain the biggest problems clearly.

## 5. Best Advice for the Australian Job Market
Give practical advice based on Australian recruiter expectations.

## 6. Resume Rewrite Suggestions
Give 10 specific resume improvements.

## 7. Top Keywords to Add or Strengthen
Give 12 important keywords or phrases.

## 8. Final Recommendation
Tell the candidate what to fix first before applying.

Do not invent experience.
Use Australian English.
"""

            cover_letter_prompt = f"""
{base_context}

Write a {cover_letter_tone} cover letter for the target role.

Requirements:
- Suitable for the Australian job market
- Natural, confident, and professional
- Not too long
- Do not invent experience
- Do not copy the job description word-for-word
- Mention work rights only if useful
- Use Australian English
"""

            recruiter_prompt = f"""
{base_context}

Write two outreach messages:

## LinkedIn Recruiter Message
Under 90 words. Friendly, polite, and professional.

## Email to Hiring Manager
Under 130 words. Clear, professional, and suitable for Australia.

Do not sound desperate.
Do not mention sponsorship unless the selected work-rights status requires it.
"""

            interview_prompt = f"""
{base_context}

Generate interview preparation content.

Use this structure:

## Technical / Role-Specific Questions
Give 5 questions with short answer tips.

## Behavioural Questions
Give 4 questions with short answer tips.

## Australian Workplace Communication Questions
Give 3 questions with short answer tips.

## Best Interview Strategy
Give practical advice for how the candidate should present themselves.
"""

            try:
                analysis = ask_ai(analysis_prompt)
                cover_letter = ask_ai(cover_letter_prompt)
                recruiter_message = ask_ai(recruiter_prompt)
                interview_questions = ask_ai(interview_prompt)

                best_cv_data = None
                best_score_data = None
                best_score = -1
                score_feedback = ""
                attempts_used = 0

                for attempt in range(1, MAX_CV_REWRITE_ATTEMPTS + 1):
                    attempts_used = attempt

                    cv_data_attempt = generate_optimised_cv_json(
                        base_context=base_context,
                        score_feedback=score_feedback
                    )

                    optimised_cv_text_attempt = cv_json_to_plain_text(cv_data_attempt)

                    score_data_attempt = calculate_score(
                        resume=optimised_cv_text_attempt,
                        job_description=final_jd_text,
                        work_rights=work_rights,
                        target_location=target_location
                    )

                    current_score = score_data_attempt["total_score"]

                    if current_score > best_score:
                        best_score = current_score
                        best_cv_data = cv_data_attempt
                        best_score_data = score_data_attempt

                    if current_score >= TARGET_CV_SCORE:
                        break

                    missing_keywords_retry = ", ".join(score_data_attempt["missing_keywords"])

                    score_feedback = f"""
The previous updated CV scored {current_score}/100, which is below the target of {TARGET_CV_SCORE}/100.

Improve the CV again by focusing on:
- Increasing keyword alignment
- Adding truthful missing keywords naturally inside the profile, skills, technical skills, and experience sections
- Strengthening the Professional Profile
- Strengthening Key Skills and Technical Skills
- Improving ATS-friendly section headings
- Adding more action-focused bullet points
- Keeping the CV suitable for Australian recruiters
- Do not create a separate "Relevant Keywords" section

Still missing or weak keywords:
{missing_keywords_retry}

Do not invent any experience, employer, dates, certifications, work rights, or numbers.
"""

                cv_data = best_cv_data
                optimised_score_data = best_score_data

                updated_cv_pdf = create_optimised_cv_pdf(
                    cv_data=cv_data,
                    target_role=target_role
                )

                st.session_state.results = {
                    "original_score_data": original_score_data,
                    "optimised_score_data": optimised_score_data,
                    "analysis": analysis,
                    "cover_letter": cover_letter,
                    "recruiter_message": recruiter_message,
                    "interview_questions": interview_questions,
                    "updated_cv_pdf": updated_cv_pdf,
                    "attempts_used": attempts_used
                }

            except Exception as error:
                st.error(f"Something went wrong while generating the CV: {error}")


# =========================
# DISPLAY RESULTS
# =========================
if st.session_state.results:
    results = st.session_state.results
    original_score_data = results["original_score_data"]
    optimised_score_data = results["optimised_score_data"]

    st.markdown("""
    <div class="glass-card">
        <div class="card-title">📊 Premium Match Dashboard</div>
        <div class="card-text">
            Your original CV score is compared with the newly optimised CV score.
        </div>
    </div>
    """, unsafe_allow_html=True)

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

    metric_1.metric(
        "Original Score",
        f"{original_score_data['total_score']}/100",
        original_score_data["band"]
    )

    metric_2.metric(
        "Updated CV Score",
        f"{optimised_score_data['total_score']}/100",
        optimised_score_data["band"]
    )

    score_improvement = optimised_score_data["total_score"] - original_score_data["total_score"]

    metric_3.metric(
        "Score Improvement",
        f"{score_improvement:+d}",
        f"{results['attempts_used']} attempt(s)"
    )

    metric_4.metric(
        "Target Score",
        f"{TARGET_CV_SCORE}/100",
        "CV target"
    )

    st.progress(
        optimised_score_data["total_score"] / 100,
        text=f"Updated CV Application Strength: {optimised_score_data['total_score']}/100"
    )

    st.markdown(f"""
    <div class="status-card">
        ✅ Ready CV PDF generated successfully. The app attempted to reach a target score of {TARGET_CV_SCORE}/100.
        Final updated CV score: {optimised_score_data['total_score']}/100.
        No fake experience, dates, employers, certifications, numbers, work rights, or keyword-dump section was added.
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        "⬇️ Download Ready Updated CV PDF",
        data=results["updated_cv_pdf"],
        file_name="ready_updated_cv_australia.pdf",
        mime="application/pdf"
    )

    breakdown_1, breakdown_2, breakdown_3, breakdown_4, breakdown_5 = st.columns(5)

    breakdown_1.metric("Keyword Alignment", f"{optimised_score_data['keyword_score']}/45")
    breakdown_2.metric("Resume Structure", f"{optimised_score_data['structure_score']}/15")
    breakdown_3.metric("Achievements", f"{optimised_score_data['achievement_score']}/10")
    breakdown_4.metric("ATS Quality", f"{optimised_score_data['ats_score']}/15")
    breakdown_5.metric("AU Market Fit", f"{optimised_score_data['au_score']}/15")

    good_col, missing_col = st.columns(2, gap="large")

    with good_col:
        st.markdown("""
        <div class="result-panel">
            <div class="card-title">✅ Updated CV Matched Keywords</div>
            <div class="card-text">These keywords appear naturally in the updated CV.</div>
        """, unsafe_allow_html=True)

        st.markdown(
            render_tags(optimised_score_data["matched_keywords"], "tag-good"),
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with missing_col:
        st.markdown("""
        <div class="result-panel">
            <div class="card-title">⚠️ Still Missing / Weak Keywords</div>
            <div class="card-text">Only add these if they are true to your experience.</div>
        """, unsafe_allow_html=True)

        st.markdown(
            render_tags(optimised_score_data["missing_keywords"], "tag-missing"),
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    tab_1, tab_2, tab_3, tab_4 = st.tabs([
        "🧠 Full Analysis",
        "📄 Cover Letter",
        "💬 Recruiter Outreach",
        "🎤 Interview Questions"
    ])

    with tab_1:
        st.markdown('<div class="result-panel">', unsafe_allow_html=True)
        st.markdown(results["analysis"])
        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            "Download Full Analysis",
            data=results["analysis"],
            file_name="ai_application_analysis_australia.txt",
            mime="text/plain"
        )

    with tab_2:
        st.markdown('<div class="result-panel">', unsafe_allow_html=True)
        st.markdown(results["cover_letter"])
        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            "Download Cover Letter",
            data=results["cover_letter"],
            file_name="cover_letter_australia.txt",
            mime="text/plain"
        )

    with tab_3:
        st.markdown('<div class="result-panel">', unsafe_allow_html=True)
        st.markdown(results["recruiter_message"])
        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            "Download Recruiter Message",
            data=results["recruiter_message"],
            file_name="recruiter_message_australia.txt",
            mime="text/plain"
        )

    with tab_4:
        st.markdown('<div class="result-panel">', unsafe_allow_html=True)
        st.markdown(results["interview_questions"])
        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            "Download Interview Questions",
            data=results["interview_questions"],
            file_name="interview_questions_australia.txt",
            mime="text/plain"
        )


# =========================
# FOOTER
# =========================
st.markdown("""
<div class="footer">
    Built with Python, Streamlit, OpenAI API, PDF/DOCX parsing, ATS scoring, Australian job market guidance, and ready CV PDF generation.
</div>
""", unsafe_allow_html=True)