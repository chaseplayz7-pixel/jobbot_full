#!/usr/bin/env python3
"""
User Preference Setup Tool
Run this script to create or update search preferences for a new user.
It will generate a customized search_control.yaml based on your inputs.
"""

import yaml
import os
from datetime import datetime

def get_user_input(prompt, default=""):
    """Get user input with a default value."""
    if default:
        response = input(f"{prompt} (default: {default}): ").strip()
        return response if response else default
    return input(f"{prompt}: ").strip()

def setup_user_preferences():
    """Interactive setup for user job search preferences."""
    print("=== Job Search Preference Setup ===")
    print("Answer the questions to customize your job search.\n")

    # User name
    user_name = get_user_input("Enter your user name (e.g., USER1)", "USER1")

    # Keywords
    print("\n--- Keywords ---")
    print("Enter job-related keywords (e.g., TPM, Data Center, Program Manager).")
    print("Separate multiple keywords with commas.")
    keywords_input = get_user_input("Keywords")
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]

    # Locations
    print("\n--- Locations ---")
    print("Enter preferred locations (e.g., Canada, Ontario, Remote).")
    print("Separate multiple locations with commas. Leave empty for all.")
    locations_input = get_user_input("Locations", "Canada")
    locations = [l.strip() for l in locations_input.split(',') if l.strip()]

    # Job sources
    print("\n--- Job Sources ---")
    print("Select which job sources to search (y/n):")
    sources = {}
    sources['jobbank'] = get_user_input("JobBank.gc.ca", "y").lower().startswith('y')
    sources['indeed'] = get_user_input("Indeed.ca", "y").lower().startswith('y')
    sources['company_ats'] = get_user_input("Company career pages", "y").lower().startswith('y')

    # Target companies
    print("\n--- Target Companies ---")
    print("Enter companies to search directly (name and career URL).")
    print("Format: Company Name|https://careers.company.com")
    print("Leave empty to skip, or enter multiple separated by semicolons.")
    companies_input = get_user_input("Companies (name|url;name|url)", "")
    target_companies = []
    if companies_input and companies_input.lower() not in ['n', 'no', 'skip']:
        for comp in companies_input.split(';'):
            if '|' in comp:
                parts = comp.split('|', 1)
                if len(parts) == 2:
                    name, url = parts
                    target_companies.append({
                        'name': name.strip(),
                        'careers': url.strip()
                    })
                else:
                    print(f"Invalid format for: {comp}. Skipping.")
            else:
                print(f"Invalid format for: {comp}. Use name|url.")

    # Scraping settings
    print("\n--- Scraping Settings ---")
    while True:
        try:
            max_jobs = int(get_user_input("Max jobs per source", "50"))
            break
        except ValueError:
            print("Please enter a number.")
    headless = get_user_input("Run browser invisibly (headless)? y/n", "y").lower().startswith('y')
    while True:
        try:
            retries = int(get_user_input("Retry failed requests", "2"))
            break
        except ValueError:
            print("Please enter a number.")

    # Output settings
    print("\n--- Output Settings ---")
    csv_file = get_user_input("Output CSV filename", f"jobs_results_{user_name}.csv")
    include_logs = get_user_input("Include detailed logs? y/n", "y").lower().startswith('y')

    # Proxy (optional)
    proxy = get_user_input("Proxy (leave empty if none)", "")

    # Generate config
    config = {
        'user': user_name,
        'created_at': datetime.utcnow().isoformat(),
        'keywords': keywords,
        'locations': locations,
        'sources': sources,
        'target_companies': target_companies,
        'scraping': {
            'max_jobs_per_source': max_jobs,
            'headless': headless,
            'retries': retries,
            'timeout': 60000
        },
        'output': {
            'csv_file': csv_file,
            'include_logs': include_logs
        },
        'proxy': proxy
    }

    return config

def save_config(config, filename='search_control.yaml'):
    """Save the config to YAML file."""
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    print(f"\nPreferences saved to {filename}")
    print("You can now run the scraper with: python playwright_full.py")

def main():
    config = setup_user_preferences()
    save_config(config)

    # Display summary
    print("\n--- Summary ---")
    print(f"User: {config['user']}")
    print(f"Keywords: {', '.join(config['keywords'])}")
    print(f"Locations: {', '.join(config['locations'])}")
    print(f"Sources: {', '.join([k for k, v in config['sources'].items() if v])}")
    print(f"Companies: {len(config['target_companies'])}")
    print(f"Output: {config['output']['csv_file']}")

if __name__ == '__main__':
    main()