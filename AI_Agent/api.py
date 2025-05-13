import os
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename # For handling filenames securely
import io # For handling file streams
import logging # Import the logging module
try:
    import PyPDF2 # For PDF text extraction
except ImportError:
    PyPDF2 = None # Handle gracefully if not installed, though it's needed for PDFs

from dotenv import load_dotenv # To load .env for the agent

# Assuming agents.py is in the same directory or accessible via PYTHONPATH
try:
    from agents import TalentEvaluationAgent
except ImportError:
    TalentEvaluationAgent = None
    print("Warning: TalentEvaluationAgent could not be imported from agents.py. Real evaluation will not work.")


app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Configure basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@app.before_request
def log_request_info():
    app.logger.debug('Request Headers: %s', request.headers)
    app.logger.debug('Request Path: %s', request.path)
    app.logger.debug('Request URL: %s', request.url)
    app.logger.debug('Request Method: %s', request.method)
    if request.method == 'POST':
        try:
            # Attempt to log form data if content type is form-data
            if request.form:
                app.logger.debug('Request Form Data: %s', request.form)
            # Attempt to log JSON data if content type is application/json
            if request.is_json:
                app.logger.debug('Request JSON Data: %s', request.get_json())
        except Exception as e:
            app.logger.debug(f"Could not log request data: {e}")


def load_job_descriptions(json_path='jobs.json'):
    if not os.path.exists(json_path):
        # Try fallback to CSV if JSON doesn't exist yet
        if os.path.exists('jobs.csv'):
            app.logger.warning(f"JSON file {json_path} not found. Falling back to jobs.csv")
            return load_job_descriptions_from_csv('jobs.csv')
        app.logger.error(f"Error: {json_path} not found and no fallback available. Serving empty job list.")
        return []
    try:
        with open(json_path, 'r') as f:
            jobs_data = json.load(f)
        
        # Ensure 'job_title' and 'description' columns exist
        required_fields = ['job_title', 'description']
        
        # Handle potential variations in job title field name
        for job in jobs_data:
            if 'Title' in job and 'job_title' not in job:
                job['job_title'] = job['Title']
            elif 'title' in job and 'job_title' not in job:
                job['job_title'] = job['title']
                
        # Check if any job has the required fields
        if not any(all(field in job for field in required_fields) for job in jobs_data):
            app.logger.error(f"Error: JSON must contain fields: {', '.join(required_fields)}")
            return []
            
        return jobs_data
    except Exception as e:
        app.logger.error(f"Error reading or processing JSON {json_path}: {e}")
        return []

def load_job_descriptions(csv_path='jobs.csv'):
    if not os.path.exists(csv_path):
        app.logger.error(f"Error: {csv_path} not found. Serving empty job list.")
        return []
    try:
        jobs_df = pd.read_csv(csv_path)
        # Ensure 'job_title' and 'description' columns exist
        required_columns = ['job_title', 'description'] # Adjust if your CSV has different names
        
        # Handle potential variations in job title column name
        if 'Title' in jobs_df.columns and 'job_title' not in jobs_df.columns:
            jobs_df.rename(columns={'Title': 'job_title'}, inplace=True)
        elif 'title' in jobs_df.columns and 'job_title' not in jobs_df.columns:
            jobs_df.rename(columns={'title': 'job_title'}, inplace=True)

        if not all(col in jobs_df.columns for col in required_columns):
            app.logger.error(f"Error: CSV must contain columns: {', '.join(required_columns)}")
            return []
            
        return jobs_df.to_dict(orient='records')
    except Exception as e:
        app.logger.error(f"Error reading or processing CSV {csv_path}: {e}")
        return []

@app.route('/api/jobs', methods=['GET'])
def get_job_titles_api():
    try:
        app.logger.info(f"Received request for /api/jobs")
        job_data = load_job_descriptions()
        job_titles = [job['job_title'] for job in job_data if 'job_title' in job and pd.notna(job['job_title'])]
        return jsonify(list(set(job_titles))) 
    except Exception as e:
        print(f"Error in /api/jobs: {e}")
        return jsonify({"error": "Could not load job titles"}), 500

def extract_text_from_resume(file_storage):
    filename = secure_filename(file_storage.filename)
    resume_text = ""
    try:
        if filename.endswith('.pdf'):
            if PyPDF2:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_storage.read()))
                for page_num in range(len(pdf_reader.pages)):
                    resume_text += pdf_reader.pages[page_num].extract_text()
            else:
                return None, "PyPDF2 is not installed, cannot process PDF."
        elif filename.endswith('.txt'):
            resume_text = file_storage.read().decode('utf-8')
        else:
            return None, "Unsupported file type. Please upload .txt or .pdf."
        
        if not resume_text.strip():
            return None, "Could not extract text from the resume or resume is empty."
            
        return resume_text, None
    except Exception as e:
        print(f"Error extracting text from {filename}: {e}")
        return None, f"Error processing file: {str(e)}"

@app.route('/api/evaluate', methods=['POST'])
def evaluate_resumes_api():
    app.logger.info(f"Received request for /api/evaluate. Path: {request.path}, URL: {request.url}")
    load_dotenv() # Load environment variables for the agent

    if 'resumes' not in request.files:
        app.logger.error("No resume files part in request to /api/evaluate")
        return jsonify({"error": "No resume files part"}), 400
    
    job_title_form = request.form.get('job_title')
    app.logger.debug(f"Job title from form: {job_title_form}")
    try:
        score_threshold_form = request.form.get('score_threshold', default=0.0, type=float)
        app.logger.debug(f"Score threshold from form: {score_threshold_form}")
    except ValueError:
        app.logger.error("Invalid score_threshold format in request to /api/evaluate")
        return jsonify({"error": "Invalid score_threshold format"}), 400
        
    if not job_title_form:
        app.logger.error("Job title is required but not provided in request to /api/evaluate")
        return jsonify({"error": "Job title is required"}), 400
        
    uploaded_files = request.files.getlist('resumes')
    app.logger.debug(f"Uploaded files: {[f.filename for f in uploaded_files]}")
    
    if not uploaded_files or uploaded_files[0].filename == '':
        app.logger.error("No selected files in request to /api/evaluate")
        return jsonify({"error": "No selected files"}), 400

    # --- Get Job Description ---
    all_jobs = load_job_descriptions()
    if not all_jobs:
         app.logger.error("Job descriptions could not be loaded from jobs.csv for /api/evaluate")
         return jsonify({"error": "Job descriptions could not be loaded from jobs.csv."}), 500

    job_to_use_for_evaluation = None
    job_description_text = None # Will be set if job_to_use_for_evaluation is found
    
    # Variables for fallback if no description is found but a URL is
    fallback_job_url = None
    fallback_matched_title = None

    for job in all_jobs:
        current_csv_job_title = job.get('job_title', '')
        # Case-insensitive partial match
        if job_title_form.lower() in current_csv_job_title.lower():
            description = job.get('description')
            
            # Check if description is valid (exists, not NaN, not just whitespace)
            is_description_valid = description and \
                                   (not isinstance(description, float) or not pd.isna(description)) and \
                                   str(description).strip()

            if is_description_valid:
                job_to_use_for_evaluation = job
                job_description_text = description
                app.logger.info(f"Found job '{current_csv_job_title}' with valid description for evaluation via partial match.")
                break # Prioritize first match with a valid description
            
            # If no job with description has been found yet, and this is the first partial match
            # with a URL, store it as a potential fallback.
            if not job_to_use_for_evaluation and not fallback_job_url:
                url_from_csv = job.get('job_url') # Assuming 'job_url' is the column name for job links
                is_url_valid = url_from_csv and \
                               (not isinstance(url_from_csv, float) or not pd.isna(url_from_csv)) and \
                               str(url_from_csv).strip()
                if is_url_valid:
                    fallback_job_url = url_from_csv
                    fallback_matched_title = current_csv_job_title
                    app.logger.info(f"Partial match '{current_csv_job_title}' found without valid description, but has URL: {url_from_csv}. Storing as fallback.")

    if job_to_use_for_evaluation:
        # A job with a valid description was found, proceed with this.
        # job_description_text is already set.
        pass
    elif fallback_job_url:
        # No job with a description found, but a partial match with a URL was found.
        app.logger.info(f"No job with description found for '{job_title_form}'. Providing URL for partially matched job '{fallback_matched_title}'.")
        return jsonify({
            "message": f"Job description for the best match '{fallback_matched_title}' is missing. You can view the job posting directly using the provided link.",
            "job_url": fallback_job_url,
            "matched_job_title": fallback_matched_title
        }), 200 # 200 OK, as we are providing information.
    else:
        # No job found with either a valid description or a fallback URL.
        app.logger.warning(f"No job found for '{job_title_form}' with a usable description or fallback URL. Returning 404.")
        return jsonify({"error": f"Could not find a suitable job posting for '{job_title_form}' with a description or direct link."}), 404
    
    # --- Initialize Agent --- (This part is reached only if job_to_use_for_evaluation is set)
    if not TalentEvaluationAgent:
        return jsonify({"error": "TalentEvaluationAgent is not available. Evaluation cannot proceed."}), 500
    
    agent = TalentEvaluationAgent()
    if not agent.is_configured(): # Assuming is_configured checks for API key
        return jsonify({"error": "Talent Evaluation Agent is not configured (e.g., API key missing)."}), 500

    results_list = []
    for file_storage in uploaded_files:
        if file_storage and file_storage.filename:
            print(f"Processing file: {file_storage.filename} for job: {job_title_form} with threshold: {score_threshold_form}")
            
            resume_text, error_msg = extract_text_from_resume(file_storage)
            if error_msg:
                results_list.append({
                    "Candidate": secure_filename(file_storage.filename), "MatchScore": 0,
                    "Assessment": error_msg, "Status": "Error",
                    "sections": [], "strengths": [], "suggestions": []
                })
                continue

            # --- Call Agent for Evaluation ---
            agent_score, agent_feedback = agent.evaluate_resume(resume_text, job_description_text)
            
            match_score = float(agent_score) * 10  # Scale 1-10 to 0-100
            assessment_text = agent_feedback

            # Simulate detailed breakdown based on agent's score and feedback
            sections_data = [
                {"name": "Relevance to Job Description", "score": int(match_score * 0.95) if match_score > 0 else 20},
                {"name": "Key Skills Match", "score": int(match_score * 1.05) if match_score > 0 and int(match_score * 1.05) <=100 else (80 if match_score > 0 else 15)},
                {"name": "Experience Alignment", "score": int(match_score * 0.9) if match_score > 0 else 10},
            ]
            # Strengths and suggestions could be parsed from agent_feedback if it's structured,
            # or use generic ones, or parts of the feedback.
            strengths_data = [f"Overall feedback indicates: {agent_feedback.split('.')[0] if '.' in agent_feedback else agent_feedback[:50]+'...'}" ]
            if match_score > 70: strengths_data.append("Good alignment with the role based on AI evaluation.")
            
            suggestions_data = ["Review the detailed AI feedback for specific improvement areas."]
            if match_score < 60 : suggestions_data.append("Consider highlighting skills more relevant to the job description.")


            results_list.append({
                "Candidate": secure_filename(file_storage.filename),
                "MatchScore": round(match_score, 2),
                "Assessment": assessment_text,
                "Status": "Processed",
                "sections": sections_data,
                "strengths": strengths_data,
                "suggestions": suggestions_data
            })
        else:
            # This case should ideally not be reached if initial checks are done
            results_list.append({
                "Candidate": "Unknown or empty file", "MatchScore": 0,
                "Assessment": "File could not be processed.", "Status": "Error",
                "sections": [], "strengths": [], "suggestions": []
            })
            
    return jsonify({"results": results_list})

# Add these imports at the top of the file if not already present
import logging
from flask import request, jsonify
from scraper import run_job_scraper

# Add this new endpoint after your existing endpoints
@app.route('/api/scrape-jobs', methods=['POST'])
def scrape_jobs_api():
    app.logger.info("Received request for /api/scrape-jobs")
    
    # Get JSON data from request
    data = request.get_json()
    if not data:
        app.logger.error("No JSON data in request to /api/scrape-jobs")
        return jsonify({"error": "No data provided"}), 400
    
    # Extract and validate parameters
    search_term = data.get('search_term')
    google_search_term = data.get('google_search_term')
    location = data.get('location')
    results_wanted = data.get('results_wanted')
    
    # Validate required parameters
    if not search_term:
        app.logger.error("Missing search_term parameter in /api/scrape-jobs request")
        return jsonify({"error": "search_term is required"}), 400
    
    if not google_search_term:
        app.logger.error("Missing google_search_term parameter in /api/scrape-jobs request")
        return jsonify({"error": "google_search_term is required"}), 400
        
    if not location:
        app.logger.error("Missing location parameter in /api/scrape-jobs request")
        return jsonify({"error": "location is required"}), 400
    
    if not results_wanted:
        app.logger.error("Missing results_wanted parameter in /api/scrape-jobs request")
        return jsonify({"error": "results_wanted is required"}), 400
    
    try:
        # Convert results_wanted to integer
        results_wanted = int(results_wanted)
        if results_wanted <= 0:
            return jsonify({"error": "results_wanted must be a positive integer"}), 400
    except ValueError:
        app.logger.error("Invalid results_wanted format in /api/scrape-jobs request")
        return jsonify({"error": "results_wanted must be a valid integer"}), 400
    
    # Optional parameters
    hours_old = data.get('hours_old', 72)
    country_indeed = data.get('country_indeed', 'USA')
    
    try:
        # Call the scraper function
        app.logger.info(f"Running job scraper with: search_term={search_term}, location={location}, results_wanted={results_wanted}")
        jobs_found = run_job_scraper(
            search_term=search_term,
            google_search_term=google_search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country_indeed
        )
        
        if jobs_found > 0:
            return jsonify({
                "message": f"Successfully scraped {jobs_found} jobs",
                "jobs_found": jobs_found
            }), 200
        elif jobs_found == 0:
            return jsonify({
                "message": "No jobs found matching your criteria",
                "jobs_found": 0
            }), 200
        else:
            return jsonify({
                "error": "An error occurred while scraping jobs",
                "jobs_found": 0
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error in /api/scrape-jobs: {str(e)}")
        return jsonify({"error": f"Failed to scrape jobs: {str(e)}"}), 500

if __name__ == '__main__':
    # It's good practice to load .env here too if running directly,
    # though the endpoint itself calls load_dotenv()
    load_dotenv() 
    app.run(debug=True, port=5001)