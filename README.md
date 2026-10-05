# AI Job Application Assistant

A Streamlit app that scores a resume against a job description with a local heuristic, then uses the OpenAI API to draft an updated CV, a cover letter, recruiter outreach, and interview preparation for the Australian job market.

Repository: https://github.com/Santo250499/ai-job-application-assistant

## Purpose

Job applications need a CV, a cover letter, a short note to a recruiter, and interview preparation, each rewritten for a different job description. This app reads a resume and a job description (uploaded or pasted), scores the match in Python, and sends that context to OpenAI. The model writes the analysis and the application drafts. The app scores each CV rewrite locally, keeps the strongest result from up to three attempts, and offers it as a downloadable PDF.

Prompts ask for Australian English and tell the model to use only details supported by the original resume. See [Limitations and notes](#limitations-and-notes) for what the app checks locally and what it leaves to the model.

## Features

- Upload a resume and a job description as PDF, DOCX, or TXT, or paste either text. When an upload contains text, that text is used and the pasted text is ignored. Extracted file text is used for scoring and generation and is not shown on the page.
- Application settings:
  - **Target role** (free text)
  - **Target location:** Australia-wide, Brisbane, Gold Coast, Sydney, Melbourne, Perth, Adelaide, Canberra, or Regional Australia
  - **Work rights / visa status:** Prefer not to say, Australian Citizen, Permanent Resident, Full Working Rights, Temporary Graduate Visa 485, Student Visa, or Requires Sponsorship
  - **Career level:** Entry Level, Junior, Mid Level, Senior, or Manager
  - **Cover letter tone:** Professional, Confident, Friendly, Formal, or Short and Direct
- Score the original resume from 0 to 100 and label it with a match band.
- Show up to 20 matched keywords and up to 20 missing or weak keywords from the job description.
- Ask the model for a markdown analysis with these sections: honest match assessment, score explanation, strongest selling points, weak areas, Australian job-market advice, 10 resume rewrite suggestions, 12 keywords to add or strengthen, and a final recommendation.
- Ask for a cover letter in the selected tone.
- Ask for a LinkedIn recruiter message (under 90 words in the prompt) and an email to a hiring manager (under 130 words in the prompt).
- Ask for interview preparation: 5 role-specific questions, 4 behavioural questions, and 3 Australian workplace communication questions, each with a short answer tip, plus an interview strategy.
- Rewrite the CV as JSON up to three times, aiming for a local score of 80 out of 100. Each rewrite can be requested again up to three times if the reply is not valid JSON. The highest-scoring draft is rendered as an A4 PDF.
- Compare the original score with the updated CV score, with a breakdown and a progress bar.
- Download:
  - `ready_updated_cv_australia.pdf`
  - `ai_application_analysis_australia.txt`
  - `cover_letter_australia.txt`
  - `recruiter_message_australia.txt`
  - `interview_questions_australia.txt`
- Stop on startup with an error if `OPENAI_API_KEY` is missing. Results from a successful run stay in the Streamlit session until the next successful run replaces them.

### How the score is calculated

Scoring does not call the API. The total is capped at 100. Match bands are Excellent Match (85 and above), Target Score Reached (80–84), Strong Match (72–79), Moderate Match (58–71), Possible Match (45–57), and Needs Major Improvement (44 and below).

| Check | Maximum | What it looks at |
| --- | --- | --- |
| Keyword alignment | 45 | Share of up to 40 job-description keywords found in the resume |
| Resume structure | 15 | Five heading checks worth 3 points each: summary or profile, experience, education, skills, and projects or certifications |
| Achievement evidence | 10 | Counts of numbers and a fixed list of action verbs, each capped before they are combined |
| ATS quality | 15 | An email pattern (3), a phone-like number (3), the word “linkedin” (2), five or more bullet or hyphen characters (3), and word count (4 points for 300–1500 words, 2 points for 220–299 or 1501–1800) |
| Australian market fit | 15 | Up to 8 points for Australian place names, work-rights phrases, and similar signals in the resume; 5 points when a work-rights option other than “Prefer not to say” is selected; 2 points when the selected city or region appears in the resume, otherwise 2 points when keyword overlap is at least 45% |

Keywords come from a fixed list of IT, support, and related phrases found in the job description, plus frequent tokens from that description. Common hiring words such as “experience” and “skills” are dropped as stopwords.

## Tech stack

| Piece | Role in this project |
| --- | --- |
| Python | Application language. The dev container image is Python 3.11. |
| [Streamlit](https://streamlit.io/) | Page layout, file upload, settings, results, and downloads |
| [OpenAI API](https://platform.openai.com/) | Text generation. `app.py` calls `gpt-4.1-mini` through the Responses API |
| python-dotenv | Loads `.env` before `OPENAI_API_KEY` is read |
| pypdf | Reads text from uploaded PDFs |
| python-docx | Reads paragraph text from uploaded DOCX files |
| ReportLab | Builds the updated CV PDF |

`requirements.txt` lists those packages with unpinned versions. `app.py` also uses the Python standard library (`os`, `re`, `json`, `html`, `io`).

## Setup and run

```bash
git clone https://github.com/Santo250499/ai-job-application-assistant.git
cd ai-job-application-assistant
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS and Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install dependencies, create a local env file, and start the app:

```bash
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Put your key in `.env`, then open [http://localhost:8501](http://localhost:8501).

### Dev Container

`.devcontainer/devcontainer.json` uses the Python 3.11 Dev Container image, installs `requirements.txt` during container setup, and on attach starts:

```bash
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false
```

Port 8501 is forwarded and labeled “Application”.

## Environment variables

`app.py` reads one environment variable, through `load_dotenv()` and `os.getenv`:

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Yes | API key passed to the OpenAI client. If it is missing, the app shows an error and stops before the form is rendered. |

`.env.example` contains a placeholder only. Copy it to `.env` and replace the placeholder. `.env` is gitignored. `.env.example` is tracked.

The resume and job description are included in the prompts sent to OpenAI when you run an analysis.

## Project structure

```text
.
├── app.py                          # Parsing, scoring, prompts, PDF layout, and the Streamlit page
├── requirements.txt                # Third-party dependencies, versions unpinned
├── .env.example                    # Placeholder for OPENAI_API_KEY
├── .gitignore
├── README.md
└── .devcontainer/
    └── devcontainer.json           # Optional Dev Container that installs dependencies and starts Streamlit
```

All of the application behaviour lives in `app.py`.

## Limitations and notes

- The match score is a local heuristic. It is a project-specific checklist, and a commercial applicant tracking system will score the same resume differently.
- Keyword checks are case-insensitive substring matches, so a short term such as `sql` or `lan` can match inside a longer word. Section checks are substring searches for words such as “education” and “skills”, so those words count even when they are not headings.
- Choosing any work-rights status other than “Prefer not to say” adds 5 Australian-market points even when the resume never states that status.
- The bullet portion of the ATS check counts `•`, `-`, and `*` anywhere in the text, including hyphens inside words.
- The CV target of 80 is a stop condition. The loop keeps the highest local score after at most three rewrites and can finish below 80.
- Instructions not to invent employers, dates, qualifications, certifications, numbers, or work rights are prompt text. The app checks that a CV reply parses as JSON. It does not compare generated claims with the source resume.
- A full run calls the API once each for the analysis, cover letter, outreach, and interview questions, then again for each CV rewrite. A rewrite that returns invalid JSON is requested up to three times.
- PDF reading uses embedded text. A scanned PDF with no text layer produces an empty result. DOCX reading uses paragraph text and skips tables, headers, and footers. TXT files are decoded as UTF-8, and invalid bytes are ignored.
- The model name `gpt-4.1-mini` is hardcoded. Dependency versions in `requirements.txt` are unpinned.
- The dev container disables Streamlit CORS and XSRF protection so the forwarded port can open. The local `streamlit run app.py` command in this README leaves those settings at Streamlit’s defaults.
- Results are kept in Streamlit session state for the current browser session.
