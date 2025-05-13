import json
import pandas as pd
from jobspy import scrape_jobs

def run_job_scraper(search_term, google_search_term, location, results_wanted, hours_old=72, country_indeed='USA'):
    """
    Run the job scraper with the provided parameters and save results to jobs.csv
    
    Args:
        search_term (str): The job title to search for
        google_search_term (str): The full search query for Google
        location (str): The location to search for jobs
        results_wanted (int): Number of job results to fetch
        hours_old (int, optional): How recent the jobs should be. Defaults to 72.
        country_indeed (str, optional): Country for Indeed search. Defaults to 'USA'.
        
    Returns:
        int: Number of jobs found, 0 if no jobs found, -1 if error occurred
    """
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "linkedin", "glassdoor"],
            search_term=search_term,
            google_search_term=google_search_term,
            location=location,
            results_wanted=int(results_wanted),
            hours_old=hours_old,
            country_indeed=country_indeed,
        )
        
        # Save to CSV
        jobs_count = len(jobs)
        if jobs_count > 0:
            jobs.to_csv("jobs.csv", index=False)
            return jobs_count
        else:
            # Create empty DataFrame with headers and save it
            empty_df = pd.DataFrame(columns=[
                'job_id', 'site', 'url', 'query', 'title', 'company', 'location', 
                'date_posted', 'salary', 'description', 'extensions'
            ])
            empty_df.to_csv("jobs.csv", index=False)
            return 0
            
    except Exception as e:
        print(f"Error in job scraper: {str(e)}")
        # Create empty DataFrame with headers on error
        try:
            empty_df = pd.DataFrame(columns=[
                'job_id', 'site', 'url', 'query', 'title', 'company', 'location', 
                'date_posted', 'salary', 'description', 'extensions'
            ])
            empty_df.to_csv("jobs.csv", index=False)
        except:
            pass
        return -1

# The original direct call is commented out
# jobs = scrape_jobs(
#     site_name=["indeed", "linkedin", "glassdoor"],
#     search_term="software engineer",
#     google_search_term="frontend developer jobs near San Francisco, CA since yesterday",
#     location="San Francisco, CA",
#     results_wanted=20,
#     hours_old=72,
#     country_indeed='USA',
# )
# print(f"Found {len(jobs)} jobs")
# print(jobs.head())
# jobs.to_csv("jobs.csv", index=False)