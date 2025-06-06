import streamlit as st
import pandas as pd
import os
import tempfile
# import json # Removed
import warnings
# from google.oauth2.service_account import Credentials # Removed
# from googleapiclient.discovery import build # Removed
# from googleapiclient.http import MediaIoBaseDownload # Removed
# import io # Removed
import PyPDF2
import docx2txt
from pathlib import Path
# import toml # Removed (only used for Drive secrets)
from dotenv import load_dotenv
from agents import TalentEvaluationAgent

# Filter out SyntaxWarnings about invalid escape sequences
warnings.filterwarnings("ignore", category=SyntaxWarning, message="invalid escape sequence")

# Load environment variables
load_dotenv()

# Set custom theme and styling
st.set_page_config(
    page_title="AI Recruiter - Talent Assessment Platform",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/manthangupta26/real-world-llm-apps',
        'Report a bug': 'https://github.com/manthangupta26/real-world-llm-apps/issues',
        'About': 'AI Recruiter - Intelligent Talent Acquisition Platform powered by Gemini AI'
    }
)

# Custom CSS
def local_css():
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            padding-top: 2rem;
            color: #ffffff;
        }
        
        /* Custom title styling */
        .title-container {
            background-color: rgba(30, 58, 138, 0.2);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .app-title {
            color: #ffffff;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0;
        }
        
        .app-subtitle {
            color: #e2e8f0;
            font-size: 1.2rem;
            font-weight: 400;
        }
        
        /* Section styling */
        .section-container {
            background-color: rgba(30, 58, 138, 0.2);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .section-title {
            color: #ffffff;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        /* Card styling for results */
        .card {
            background-color: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            color: #ffffff;
        }
        
        .card h4 {
            color: #ffffff;
            margin-top: 0;
        }
        
        .card p {
            color: #e2e8f0;
        }
        
        .card-pass {
            border-left: 5px solid #4CAF50;
        }
        
        .card-fail {
            border-left: 5px solid #F44336;
        }
        
        .card-error {
            border-left: 5px solid #FF9800;
        }
        
        .score-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-weight: 600;
            font-size: 0.9rem;
            color: white;
        }
        
        .badge-pass {
            background-color: #4CAF50;
        }
        
        .badge-fail {
            background-color: #F44336;
        }
        
        .badge-error {
            background-color: #FF9800;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        /* Radio buttons and sliders */
        .stRadio > div {
            padding: 10px;
            border-radius: 5px;
            background-color: rgba(30, 41, 59, 0.7);
            color: #ffffff;
        }
        
        /* Text inputs and areas */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: rgba(30, 41, 59, 0.7);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* File uploader */
        .stFileUploader > div > div {
            padding: 10px;
            border-radius: 5px;
            background-color: rgba(30, 41, 59, 0.7);
            color: #ffffff;
        }
        
        .uploadedFile {
            background-color: rgba(30, 41, 59, 0.7) !important;
            color: #ffffff !important;
        }
        
        /* Processing info */
        .processing-info {
            padding: 1rem;
            border-radius: 5px;
            background-color: rgba(13, 110, 253, 0.2);
            margin-bottom: 1rem;
            border-left: 5px solid #0d6efd;
            color: #ffffff;
        }
        
        /* Footer styling */
        .footer {
            text-align: center;
            padding: 1rem;
            color: #e2e8f0;
            font-size: 0.9rem;
            margin-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #e2e8f0 !important;
        }
        
        [data-testid="stMetricDelta"] {
            color: #e2e8f0 !important;
        }
        
        /* Info boxes */
        .stAlert {
            background-color: rgba(30, 41, 59, 0.7) !important;
            color: #ffffff !important;
        }
        
        /* Remove Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Make sure all text is visible */
        p, h1, h2, h3, h4, h5, h6, span, label, .stMarkdown, .stText {
            color: #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
# Initialize styling
local_css()

# Initialize the resume evaluation agent
@st.cache_resource
def get_resume_agent():
    agent = TalentEvaluationAgent()
    if not agent.is_configured():
        st.error("Gemini API key not found. Please set the GEMINI_API_KEY in your .env file.")
        st.stop()
    return agent

# Function to authenticate with Google Drive # Removed
# @st.cache_resource
# def get_drive_service():
#     # First try to get credentials from Streamlit secrets
#     try:
#         uploaded_json = st.secrets.get("google_credentials", None)
#         
#         if uploaded_json:
#             credentials = Credentials.from_service_account_info(uploaded_json)
#             drive_service = build('drive', 'v3', credentials=credentials)
#             return drive_service
#     except FileNotFoundError:
#         # If streamlit can't find secrets.toml in the default locations, try loading it manually
#         local_secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
#         if os.path.exists(local_secrets_path):
#             try:
#                 secrets_data = toml.load(local_secrets_path)
#                 if 'google_credentials' in secrets_data:
#                     credentials = Credentials.from_service_account_info(secrets_data['google_credentials'])
#                     drive_service = build('drive', 'v3', credentials=credentials)
#                     return drive_service
#             except Exception as e:
#                 st.error(f"Error loading secrets from {local_secrets_path}: {str(e)}")
#     
#     # If not found in secrets, try from environment variables
#     env_creds = {}
#     
#     # Check for Google Drive environment variables
#     required_keys = [
#         "GOOGLE_DRIVE_TYPE", "GOOGLE_DRIVE_PROJECT_ID", "GOOGLE_DRIVE_PRIVATE_KEY_ID",
#         "GOOGLE_DRIVE_PRIVATE_KEY", "GOOGLE_DRIVE_CLIENT_EMAIL", "GOOGLE_DRIVE_CLIENT_ID",
#         "GOOGLE_DRIVE_AUTH_URI", "GOOGLE_DRIVE_TOKEN_URI", 
#         "GOOGLE_DRIVE_AUTH_PROVIDER_CERT_URL", "GOOGLE_DRIVE_CLIENT_CERT_URL"
#     ]
#     
#     # Check if all required environment variables are present
#     all_keys_present = all(os.getenv(key) for key in required_keys)
#     
#     if all_keys_present:
#         # Create credentials from environment variables
#         env_creds = {
#             "type": os.getenv("GOOGLE_DRIVE_TYPE"),
#             "project_id": os.getenv("GOOGLE_DRIVE_PROJECT_ID"),
#             "private_key_id": os.getenv("GOOGLE_DRIVE_PRIVATE_KEY_ID"),
#             "private_key": os.getenv("GOOGLE_DRIVE_PRIVATE_KEY").replace("\\n", "\n"),
#             "client_email": os.getenv("GOOGLE_DRIVE_CLIENT_EMAIL"),
#             "client_id": os.getenv("GOOGLE_DRIVE_CLIENT_ID"),
#             "auth_uri": os.getenv("GOOGLE_DRIVE_AUTH_URI"),
#             "token_uri": os.getenv("GOOGLE_DRIVE_TOKEN_URI"),
#             "auth_provider_x509_cert_url": os.getenv("GOOGLE_DRIVE_AUTH_PROVIDER_CERT_URL"),
#             "client_x509_cert_url": os.getenv("GOOGLE_DRIVE_CLIENT_CERT_URL")
#         }
#         
#         try:
#             credentials = Credentials.from_service_account_info(env_creds)
#             drive_service = build('drive', 'v3', credentials=credentials)
#             return drive_service
#         except Exception as e:
#             st.error(f"Error loading Google Drive credentials from environment variables: {str(e)}")
#     
#     st.error("""
#     Google Drive credentials not found. Please either:
#     
#     1. Set up credentials in Streamlit secrets (.streamlit/secrets.toml)
#     2. Or provide credentials in your .env file
#     
#     See the README.md for detailed instructions.
#     """)
#     return None

# Function to extract text from a PDF file
def extract_text_from_pdf(file_obj):
    pdf_reader = PyPDF2.PdfReader(file_obj)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Function to extract text from a DOCX file
def extract_text_from_docx(file_obj):
    return docx2txt.process(file_obj)

# Function to extract text from uploaded files
def extract_text_from_file(file_obj, file_extension=None):
    # If file_extension is not provided, try to get it from the file object
    if file_extension is None:
        try:
            file_extension = Path(file_obj.name).suffix.lower()
        except AttributeError:
            # If file_obj doesn't have a name attribute (like BytesIO), the extension must be provided
            st.error("Could not determine file type. Please provide file extension.")
            return None
    else:
        # Ensure the extension starts with a dot
        if not file_extension.startswith('.'):
            file_extension = '.' + file_extension
        file_extension = file_extension.lower()
    
    if file_extension == ".pdf":
        return extract_text_from_pdf(file_obj)
    elif file_extension == ".docx":
        return extract_text_from_docx(file_obj)
    elif file_extension == ".txt":
        return file_obj.read().decode('utf-8')
    else:
        return None

# Function to download file from Google Drive # Removed
# def download_file_from_drive(drive_service, file_id):
#     request = drive_service.files().get_media(fileId=file_id)
#     file_content = io.BytesIO()
#     downloader = MediaIoBaseDownload(file_content, request)
#     done = False
#     while not done:
#         status, done = downloader.next_chunk()
#     file_content.seek(0)
#     return file_content

# Function to list files in a Google Drive folder # Removed
# def list_files_in_folder(drive_service, folder_id):
#     results = []
#     page_token = None
#     
#     while True:
#         response = drive_service.files().list(
#             q=f"'{folder_id}' in parents and trashed=false",
#             spaces='drive',
#             fields='nextPageToken, files(id, name, mimeType)',
#             pageToken=page_token
#         ).execute()
#         
#         for file in response.get('files', []):
#             results.append(file)
#         
#         page_token = response.get('nextPageToken', None)
#         if not page_token:
#             break
#             
#     return results

# Function to extract file ID from Google Drive link # Removed
# def extract_file_id(drive_link):
#     if "drive.google.com" in drive_link:
#         if "/file/d/" in drive_link:
#             # Format: https://drive.google.com/file/d/FILE_ID/view
#             file_id = drive_link.split("/file/d/")[1].split("/")[0]
#         elif "id=" in drive_link:
#             # Format: https://drive.google.com/open?id=FILE_ID
#             file_id = drive_link.split("id=")[1].split("&")[0]
#         elif "/folders/" in drive_link:
#             # Format: https://drive.google.com/drive/folders/FOLDER_ID
#             file_id = drive_link.split("/folders/")[1].split("?")[0].split("/")[0]
#         else:
#             return None
#         return file_id
#     return None

# Function to load job descriptions from CSV
def load_job_descriptions(csv_path="jobs.csv"):
    try:
        df = pd.read_csv(csv_path)
        # Check if required columns exist
        if 'title' not in df.columns or 'description' not in df.columns:
            st.error(f"Error: CSV file '{csv_path}' must contain 'title' and 'description' columns.")
            return None, None
        # Create a dictionary mapping titles to descriptions
        job_data = df.set_index('title')['description'].to_dict()
        return list(job_data.keys()), job_data
    except FileNotFoundError:
        st.error(f"Error: Job description file '{csv_path}' not found. Please place it in the application directory.")
        return None, None
    except Exception as e:
        st.error(f"Error reading job descriptions from CSV: {e}")
        return None, None

# Function to display results
def display_results(results, score_threshold):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">Evaluation Results</h2>', unsafe_allow_html=True)

    if not results:
        st.info("No resumes were processed.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    df = pd.DataFrame(results)

    # Separate qualified, not qualified, and error candidates
    qualified = df[df['Status'] == 'Qualified']
    not_qualified = df[df['Status'] == 'Not Qualified']
    errors = df[df['Status'] == 'Error']

    if qualified.empty and not_qualified.empty and errors.empty:
         st.info("Processing completed, but no results were generated.")
    elif qualified.empty and not_qualified.empty:
        st.warning("All resumes resulted in errors during processing.")
    elif qualified.empty:
        st.info(f"No candidates matched your qualifications threshold of {score_threshold}. Consider adjusting your threshold or job requirements.")
    else:
        st.success(f"{len(qualified)} candidate(s) meet or exceed the qualification threshold of {score_threshold}.")

    # Display Qualified Candidates
    st.markdown('<h3 style="color: #4CAF50; margin-top: 20px;">Qualified Candidates</h3>', unsafe_allow_html=True)
    qualified_df = df[df["Status"] == "Qualified"].sort_values(by="Match Score", ascending=False).reset_index(drop=True)
    
    if not qualified_df.empty:
        for _, row in qualified_df.iterrows():
            st.markdown(
                f"""
                <div class="card card-pass">
                    <h4>{row['Candidate']}</h4>
                    <p><span class="score-badge badge-pass">Match Score: {row['Match Score']:.1f}/10</span></p>
                    <p><strong>Assessment:</strong> {row['Assessment']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    else:
        st.info(f"No candidates matched your qualifications threshold of {score_threshold}. Consider adjusting your threshold or job requirements.")
    
    # Display failed resumes
    st.markdown('<h3 style="color: #F44336; margin-top: 20px;">Non-Qualified Candidates</h3>', unsafe_allow_html=True)
    not_qualified_df = df[df["Status"] == "Not Qualified"].sort_values(by="Match Score", ascending=False).reset_index(drop=True)
    
    if not not_qualified_df.empty:
        for _, row in not_qualified_df.iterrows():
            st.markdown(
                f"""
                <div class="card card-fail">
                    <h4>{row['Candidate']}</h4>
                    <p><span class="score-badge badge-fail">Match Score: {row['Match Score']:.1f}/10</span></p>
                    <p><strong>Assessment:</strong> {row['Assessment']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    else:
        st.info("All candidates have met your qualification threshold.")
    
    # Display error resumes
    error_df = df[df["Status"] == "Error"].reset_index(drop=True)
    if not error_df.empty:
        st.markdown('<h3 style="color: #FF9800; margin-top: 20px;">Processing Errors</h3>', unsafe_allow_html=True)
        for _, row in error_df.iterrows():
            st.markdown(
                f"""
                <div class="card card-error">
                    <h4>{row['Candidate']}</h4>
                    <p><span class="score-badge badge-error">Error</span></p>
                    <p><strong>Message:</strong> {row['Assessment']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Download results as CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Talent Assessment Report",
        data=csv,
        file_name="ai_recruiter_talent_assessment.csv",
        mime="text/csv"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)


# Main app
def main():
    # Custom title
    st.markdown(
        """
        <div class="title-container">
            <h1 class="app-title">AI Recruiter 👔</h1>
            <p class="app-subtitle">Intelligent Talent Acquisition Powered by AI</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Initialize the resume evaluation agent
    resume_agent = get_resume_agent()

    # Load job descriptions
    job_titles, job_descriptions_map = load_job_descriptions()

    # Stop execution if job descriptions failed to load
    if job_titles is None or job_descriptions_map is None:
        return

    # Create two columns for layout
    col1, col2 = st.columns([1, 1])

    job_description = None # Initialize job_description

    with col1:
        # Job Description Section
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Select Position</h2>', unsafe_allow_html=True)

        # Use a selectbox for job titles
        selected_title = st.selectbox(
            "Choose the job position:",
            options=job_titles,
            index=0, # Default to the first job
            help="Select the job you want to evaluate candidates for."
        )

        # Get the corresponding description
        if selected_title:
            job_description = job_descriptions_map[selected_title]
            # Optionally display the selected description (read-only)
            st.text_area(
                "Selected Job Description:",
                value=job_description,
                height=250, # Adjust height as needed
                disabled=True,
                key="job_desc_display" # Add a key to prevent state issues
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # Evaluation Settings Section
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Candidate Evaluation Settings</h2>', unsafe_allow_html=True)
        score_threshold = st.slider(
            "Qualification threshold (out of 10):",
            min_value=1.0,
            max_value=10.0,
            value=7.5,
            step=0.1,
            help="Candidates with scores above this threshold will be marked as 'Qualified'"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Resume Input Section
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Candidate Resumes</h2>', unsafe_allow_html=True)

        # Remove the radio button for input method
        # input_method = st.radio(
        #     "Choose how to upload candidate resumes:",
        #     ("Upload files directly", "Google Drive link"), # Removed Google Drive option
        #     horizontal=True
        # )

        # Always use file uploader now
        # if input_method == "Upload files directly": # Condition removed
        uploaded_files = st.file_uploader(
            "Upload candidate resumes (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="You can select multiple files at once to batch process candidates"
        )

        if uploaded_files:
            st.success(f"{len(uploaded_files)} candidate resume(s) uploaded successfully!")

        # Removed the Google Drive input section
        # else:  # Google Drive link
        #     # ... removed code ...

        # Evaluate button
        evaluate_button = st.button("Evaluate Candidates", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Process resumes when button is clicked
    if evaluate_button and job_description: # Check if a job description is selected
        with st.spinner("Initializing talent evaluation process..."):
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<h2 class="section-title">Talent Evaluation Process</h2>', unsafe_allow_html=True)

            # Only process uploaded files now
            # if input_method == "Upload files directly": # Condition removed
            if not uploaded_files:
                st.warning("Please upload at least one candidate resume.")
                st.markdown('</div>', unsafe_allow_html=True)
                return # Use return instead of st.stop() inside main()

            results = []
            progress_text = st.empty()
            progress_bar = st.progress(0)

            for i, file in enumerate(uploaded_files):
                progress_text.markdown(f'<div class="processing-info">Analyzing candidate: {file.name} ({i+1}/{len(uploaded_files)})</div>', unsafe_allow_html=True)
                resume_text = extract_text_from_file(file)

                if resume_text:
                    with st.spinner(f"AI is evaluating candidate {file.name}..."):
                        score, feedback = resume_agent.evaluate_resume(resume_text, job_description)

                        results.append({
                            "Candidate": file.name,
                            "Match Score": score,
                            "Assessment": feedback,
                            "Status": "Qualified" if score >= score_threshold else "Not Qualified"
                        })
                else:
                    results.append({
                        "Candidate": file.name,
                        "Match Score": 0,
                        "Assessment": "Could not extract text from resume file.",
                        "Status": "Error"
                    })

                progress_bar.progress((i + 1) / len(uploaded_files))

            progress_text.empty()
            display_results(results, score_threshold)

            # Removed the Google Drive processing block
            # else:  # Google Drive link
            #     # ... removed code ...

            st.markdown('</div>', unsafe_allow_html=True) # Close section container

    elif evaluate_button and not job_description:
         st.warning("Please select a job position first.")


    # Footer
    st.markdown(
        """
        <div class="footer">
            <p>AI Recruiter | Intelligent Talent Acquisition Platform | Powered by Gemini AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()