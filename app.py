import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Job Application Assistant")
st.write("Paste your resume and job description to get a match score, improvement tips, cover letter, LinkedIn message, and interview questions.")

resume = st.text_area("Paste Your Resume Here", height=250)
job_description = st.text_area("Paste Job Description Here", height=250)

def ask_ai(prompt):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert career coach, resume reviewer, ATS specialist, and recruiter."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4
    )

    return response.choices[0].message.content


if st.button("Analyze Application"):
    if not resume or not job_description:
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
            Write a professional tailored cover letter based on this resume and job description.

            Resume:
            {resume}

            Job Description:
            {job_description}

            Make it confident, professional, and not too long.
            """

            linkedin_prompt = f"""
            Write a short LinkedIn message to a recruiter for this job.

            Resume:
            {resume}

            Job Description:
            {job_description}

            Keep it friendly, professional, and under 100 words.
            """

            interview_prompt = f"""
            Generate 10 likely interview questions based on this resume and job description.

            Resume:
            {resume}

            Job Description:
            {job_description}

            Include technical, behavioural, and role-specific questions.
            """

            analysis = ask_ai(analysis_prompt)
            cover_letter = ask_ai(cover_letter_prompt)
            linkedin_message = ask_ai(linkedin_prompt)
            interview_questions = ask_ai(interview_prompt)

            st.subheader("📊 Resume Match Analysis")
            st.write(analysis)

            st.subheader("📄 Tailored Cover Letter")
            st.write(cover_letter)

            st.subheader("💬 LinkedIn Recruiter Message")
            st.write(linkedin_message)

            st.subheader("🎤 Interview Questions")
            st.write(interview_questions)