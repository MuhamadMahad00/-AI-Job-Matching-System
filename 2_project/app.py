import streamlit as st
import requests
import json
import time

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/analyze"

st.set_page_config(
    page_title="AI Job Matcher",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Global Styles */
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        color: #FAFAFA;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Job Card Styling */
    .job-card {
        background-color: #262730; /* Dark card background */
        color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 6px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.4);
    }
    
    .job-card h3 {
        color: #FAFAFA !important;
        margin-bottom: 0.5rem;
    }
    
    .job-card p {
        color: #E0E0E0;
        margin-bottom: 0.5rem;
    }

    /* Accents */
    .match-score {
        font-size: 1.1rem;
        font-weight: bold;
        color: #69F0AE; /* Bright Green */
        background-color: rgba(105, 240, 174, 0.1);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        display: inline-block;
    }
    
    .missing-skills {
        color: #FF5252; /* Bright Red */
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("AI Career Agent")
    st.write("Upload your resume to find your perfect job match.")
    st.info("Supported formats: PDF, DOCX")

# --- Main Content ---
st.markdown('<div class="main-header">🚀 AI-Powered Job Matching System</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    # Initialize session state for results if not present
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    
    if st.button("Analyze Resume & Find Matches"):
        st.session_state.analysis_results = None  # Clear old results
        with st.spinner("AI Agents are analyzing your profile..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(API_URL, files=files)
                
                if response.status_code == 200:
                    st.session_state.analysis_results = response.json()
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend. Is the server running?")
            except Exception as e:
                st.error(f"An error occurred: {e}")
                if "GEMINI_API_KEY" in str(e) or "500" in str(e):
                    st.error("🚨 It seems like the API Key is missing or invalid. Please check your **.env** file.")

    # Display Results from Session State
    if st.session_state.analysis_results:
        data = st.session_state.analysis_results
        top_jobs = data.get("top_jobs", [])
        career_report = data.get("career_report", "")
        
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🎯 Top Job Matches")
            if not top_jobs:
                st.warning("No matches found. Try adding more details to your resume.")
            
            for job in top_jobs:
                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <h3>{job['title']}</h3>
                        <p><strong>📍 Location:</strong> {job['location']}</p>
                        <p><span class="match-score">Match Score: {job['match_percentage']}%</span></p>
                        <p><strong>⚠️ Missing Skills:</strong> <span class="missing-skills">{', '.join(job['details']['missing_skills'])}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("View Details"):
                        st.write(f"**Semantic Score:** {job['details']['semantic_score']}")
                        st.write(f"**Skill Match:** {job['details']['skill_match']}")
                        
        with col2:
            st.subheader("📝 AI Career Report")
            st.markdown(career_report)
            
            st.download_button(
                label="Download Report",
                data=career_report,
                file_name="career_report.md",
                mime="text/markdown"
            )

else:
    st.info("Please upload a resume to get started.")

# Footer
st.markdown("---")
st.markdown("Powered by Google Gemini & FAISS | Built with FastAPI & Streamlit")
