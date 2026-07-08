import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load API key from .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Job Application Assistant")
st.write(
    "Paste your resume and job description to get a match score, resume tips, "
    "cover letter, LinkedIn message, and interview questions."
)

# Stop the app if API key is missing
if not api_key:
    st.error("OPENAI_API_KEY is missing. Please add it to your .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

# Inputs
resume = st.text_area("Paste Your Resume Here", height=250)
job_description = st.text_area("Paste Job Description Here", height=250)

# Day 5 Challenge: Tone dropdown
tone = st.selectbox(
    "Choose Cover Letter Tone",
    ["Professional", "Confident", "Friendly", "Formal", "Short and Direct"]
)

def ask_ai(prompt):
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=(
                "You are an expert career coach, resume reviewer, ATS specialist, "
                "and recruiter. Give practical, honest, and specific advice."
            ),
            input=prompt,
            temperature=0.4
        )

        return response.output_text

    except Exception as e:
        return f"Error: {e}"


if st.button("Analyze Application"):
    if not resume.strip() or not job_description.strip():
        st.warning("Please paste both your resume and the job description.")
    else:
        with st.spinner("Analyzing your application..."):

            analysis_prompt = f"""
Analyze the resume against the job description.

Resume:
{resume}

Job Description:
{job_description}

Provide the response using this structure:

1. Match Score out of 100
2. Overall Suitability
3. Key Strengths
4. Missing Keywords
5. Resume Improvement Suggestions
6. ATS Optimization Tips
7. Final Recommendation

Be practical, honest, and specific.
"""

            cover_letter_prompt = f"""
Write a {tone} tailored cover letter based on this resume and job description.

Resume:
{resume}

Job Description:
{job_description}

Requirements:
- Make it suitable for a real job application
- Do not make it too long
- Use a confident but natural tone
- Do not copy the job description word-for-word
"""

            linkedin_prompt = f"""
Write a short LinkedIn message to a recruiter for this job.

Resume:
{resume}

Job Description:
{job_description}

Requirements:
- Keep it under 100 words
- Make it friendly and professional
- Mention interest in the role
- Ask politely for consideration or referral
"""

            interview_prompt = f"""
Generate 10 likely interview questions based on this resume and job description.

Resume:
{resume}

Job Description:
{job_description}

Include:
- Technical questions
- Behavioural questions
- Role-specific questions
"""

            analysis = ask_ai(analysis_prompt)
            cover_letter = ask_ai(cover_letter_prompt)
            linkedin_message = ask_ai(linkedin_prompt)
            interview_questions = ask_ai(interview_prompt)

            tab1, tab2, tab3, tab4 = st.tabs(
                [
                    "📊 Resume Analysis",
                    "📄 Cover Letter",
                    "💬 LinkedIn Message",
                    "🎤 Interview Questions"
                ]
            )

            with tab1:
                st.subheader("📊 Resume Match Analysis")
                st.markdown(analysis)

            with tab2:
                st.subheader("📄 Tailored Cover Letter")
                st.markdown(cover_letter)

                st.download_button(
                    label="Download Cover Letter",
                    data=cover_letter,
                    file_name="cover_letter.txt",
                    mime="text/plain"
                )

            with tab3:
                st.subheader("💬 LinkedIn Recruiter Message")
                st.markdown(linkedin_message)

            with tab4:
                st.subheader("🎤 Interview Questions")
                st.markdown(interview_questions)