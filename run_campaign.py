#!/usr/bin/env python3
import os
import sys
import csv
import json
import argparse
import subprocess
import time
import urllib.request
import re
from PIL import Image

# ROOT_DIR is the root of the project where this global script resides
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_active_session_dir():
    """
    Reads the global '.active_session' pointer file in the root directory 
    to dynamically resolve which session folder is currently active.
    """
    pointer_path = os.path.join(ROOT_DIR, ".active_session")
    if not os.path.exists(pointer_path):
        return None
    with open(pointer_path, "r", encoding="utf-8") as f:
        path = f.read().strip()
        if os.path.exists(path):
            return path
    return None

def load_session_state(session_dir):
    state_path = os.path.join(session_dir, "session_state.json")
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "session_id": os.path.basename(session_dir),
        "status": "initialized",
        "accumulated_feedback": []
    }

def save_session_state(session_dir, state):
    state_path = os.path.join(session_dir, "session_state.json")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def show_feedback_history(state):
    print("\n" + "="*50)
    print("ACTIVE ACCUMULATED FEEDBACK HISTORY:")
    if not state["accumulated_feedback"]:
        print(" (No historical corrections applied yet.)")
    for i, fb in enumerate(state["accumulated_feedback"], 1):
        print(f" [{i}] {fb}")
    print("="*50 + "\n")

def clear_feedback_history(session_dir, state):
    state["accumulated_feedback"] = []
    save_session_state(session_dir, state)
    print("✔ Accumulated feedback history has been successfully reset.")

def generate_leads_batch(leads_path, count, mode):
    if not os.path.exists(leads_path):
        print(f"Error: Leads file not found at {leads_path}")
        return []
        
    leads = []
    with open(leads_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
            
    if mode == "sample":
        return leads[:count]
    else:
        return leads

def compile_lead_html(session_dir, company_name, config_path):
    company_clean = company_name.lower().replace(" ", "_")
    output_html = os.path.join(session_dir, f"{company_clean}_demo.html")
    compiler_path = os.path.join(ROOT_DIR, "compile_onboarder.py")
    
    cmd = [sys.executable, compiler_path, config_path, output_html]
    try:
        subprocess.run(cmd, check=True)
        return output_html
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to compile HTML for {company_name}: {e}")
        return None

def download_and_convert_favicon(session_dir, company_name, website):
    """
    Programmatically extracts the domain, bypasses anti-scraping firewalls 
    using browser user-agent spoofing, scrapes HTML for favicon tags if needed,
    and converts downloaded ICO/JPG/PNG images into high-compatibility PNG format.
    """
    company_clean = company_name.lower().replace(" ", "_")
    output_path = os.path.join(session_dir, f"{company_clean}_icon.png")
    
    # 1. Extract domain
    domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].strip()
    if not domain:
        print(f"   ✖ Invalid domain extracted from website: '{website}'")
        return None
        
    print(f"   Resolving corporate favicon for: {domain}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Candidate URLs to search
    candidates = [
        f"https://{domain}/favicon.ico",
        f"https://www.{domain}/favicon.ico",
        f"https://{domain}/favicon.png",
        f"https://www.{domain}/favicon.png",
    ]
    
    # Scrape the home page HTML first to find WordPress or CMS explicit icon paths
    try:
        home_url = f"https://{domain}"
        req = urllib.request.Request(home_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Use regex to search for link icon tags
            match = re.search(r'<link[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not match:
                # Try search by matching Apple Touch Icons if favicon is missing
                match = re.search(r'<link[^>]*rel=["\']apple-touch-icon["\'][^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
                
            if match:
                href = match.group(1).strip()
                # Resolve relative URL path schemas
                if href.startswith("//"):
                    resolved_url = "https:" + href
                elif href.startswith("/"):
                    resolved_url = f"https://{domain}" + href
                elif not href.startswith("http"):
                    resolved_url = f"https://{domain}/" + href
                else:
                    resolved_url = href
                candidates.insert(0, resolved_url) # Put scraped path as the #1 priority candidate!
    except Exception as e:
        # Home page scraping failed, proceed with standard fallback candidates
        pass
        
    # Attempt downloads on prioritized candidate list
    for url in candidates:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read()
                
                # Write to temp file for Pillows validation
                temp_filename = os.path.join(session_dir, f"temp_{company_clean}_favicon")
                with open(temp_filename, "wb") as f:
                    f.write(content)
                    
                # Load with PIL to verify and convert
                with Image.open(temp_filename) as img:
                    img.load()
                    # Convert to standard RGBA format and save as standard high-compatibility PNG
                    img.convert("RGBA").save(output_path, "PNG")
                    
                os.remove(temp_filename)
                print(f"   ✔ Favicon downloaded successfully from: {url}")
                return output_path
        except Exception as e:
            if os.path.exists(os.path.join(session_dir, f"temp_{company_clean}_favicon")):
                try: os.remove(os.path.join(session_dir, f"temp_{company_clean}_favicon"))
                except: pass
            continue
            
    print(f"   ⚠ Warning: Failed to download favicon for {company_name}. Using monogram initials fallback.")
    return None

def upload_assets_to_s3(session_dir, company_name, html_path):
    """
    Deploys compiled HTML pages and icons to the public S3 assets bucket.
    Explicitly forces accurate MIME content-types to ensure browsers render pages natively rather than downloading them.
    STRICT COMPLIANCE: If any S3 upload command fails, the exception is raised with the detailed AWS stderr,
    and program execution is aborted immediately.
    """
    import uuid
    company_clean = company_name.lower().replace(" ", "_")
    random_uuid = str(uuid.uuid4())
    s3_dir = f"s3://elvity-public-assets/viz/{random_uuid}"
    public_url_base = f"https://www.elvity.ai/viz/{random_uuid}/{company_clean}_demo.html"
    
    print(f"   Deploying assets to S3 bucket: {s3_dir}...")
    
    # 1. Upload HTML pagelet (Set explicit text/html MIME type)
    try:
        cmd_html = ["aws", "s3", "cp", html_path, f"{s3_dir}/{company_clean}_demo.html", "--content-type", "text/html"]
        res = subprocess.run(cmd_html, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"✖ Critical Error: S3 HTML upload failed for {company_name}! AWS CLI Error:")
        print(e.stderr)
        raise RuntimeError(f"S3 Upload Failure (HTML): {e.stderr}")
        
    # 2. Upload Elvity Icon (Using absolute path and forcing image/png MIME type)
    elvity_icon_path = os.path.join(ROOT_DIR, "elvity-icon.png")
    try:
        cmd_elv = ["aws", "s3", "cp", elvity_icon_path, f"{s3_dir}/elvity-icon.png", "--content-type", "image/png"]
        res = subprocess.run(cmd_elv, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"✖ Critical Error: S3 shared icon upload failed! AWS CLI Error:")
        print(e.stderr)
        raise RuntimeError(f"S3 Upload Failure (Shared Icon): {e.stderr}")
        
    # 3. Upload Client Icon (Set explicit image/png MIME type)
    client_icon_path = os.path.join(session_dir, f"{company_clean}_icon.png")
    if os.path.exists(client_icon_path):
        try:
            cmd_icon = ["aws", "s3", "cp", client_icon_path, f"{s3_dir}/{company_clean}_icon.png", "--content-type", "image/png"]
            res = subprocess.run(cmd_icon, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"✖ Critical Error: S3 client icon upload failed for {company_name}! AWS CLI Error:")
            print(e.stderr)
            raise RuntimeError(f"S3 Upload Failure (Client Icon): {e.stderr}")
            
    print(f"   ✔ S3 upload successful! Public URL: {public_url_base}")
    return public_url_base

def run_gemini_inference(lead, system_instructions):
    try:
        import google.generativeai as genai
    except ImportError:
        print("Error: 'google-generativeai' package is not installed!")
        print("Please run: pip install google-generativeai")
        return None
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set!")
        return None
        
    genai.configure(api_key=api_key)
    
    # In google-generativeai, system_instruction must be passed to the GenerativeModel constructor
    model = genai.GenerativeModel("gemini-3.5-flash", system_instruction=system_instructions)
    
    prompt = f"""
    Analyze the following B2B sales prospect metadata and generate the campaign emails and customized uploader tables:
    
    Company: {lead.get('Company Name', 'Unknown')}
    Website: {lead.get('Website', 'Unknown')}
    Role: {lead.get('Title', 'Unknown')}
    First Name: {lead.get('First Name', 'Unknown')}
    Last Name: {lead.get('Last Name', 'Unknown')}
    
    Ensure that the generated messages and database structures are highly context-aware, customized specifically to their industry workflows, and fully compliant with our system instructions.
    """
    
    try:
        response = model.generate_content(
            contents=prompt,
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"API Call Failed for {lead.get('Company Name')}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Elvity Account-Based Campaign Automation Engine")
    parser.add_argument("--mode", choices=["init", "sample", "bulk"], required=True,
                        help="Campaign execution phase: 'init' to setup, 'sample' for dry-runs, 'bulk' for full batch execution.")
    parser.add_argument("--count", type=int, default=4,
                        help="Number of leads to process during the sampling phase (default: 4).")
    parser.add_argument("--feedback", type=str, default=None,
                        help="Add a new conversational design correction to the accumulative feedback ledger.")
    parser.add_argument("--show-feedback", action="store_true",
                        help="Print the active list of accumulated design guidelines.")
    parser.add_argument("--clear-feedback", action="store_true",
                        help="Reset the accumulative feedback history back to standard instructions.")
    parser.add_argument("--leads-csv", type=str, default="new_leads.csv",
                        help="Path to the source leads CSV file (default: 'new_leads.csv').")
                        
    args = parser.parse_args()
    
    # Resolve active session directory pointers
    if args.mode == "init":
        # Create a new timestamped folder
        timestamp = time.strftime("%Y-%m-%d-%H%M")
        session_dir = os.path.join(ROOT_DIR, "sessions", timestamp)
        os.makedirs(session_dir, exist_ok=True)
        
        print("\n" + "="*50)
        print(f"INITIALIZING NEW CAMPAIGN LIFECYCLE")
        print(f"Generated Session Directory: {session_dir}")
        
        state = {
            "session_id": timestamp,
            "status": "initialized",
            "accumulated_feedback": []
        }
        save_session_state(session_dir, state)
        
        # Write active session pointer file to root
        with open(os.path.join(ROOT_DIR, ".active_session"), "w") as f:
            f.write(session_dir)
        print("✔ Session initialized. Pointer file '.active_session' saved to root.")
        print("="*50 + "\n")
        sys.exit(0)

    # For sample/bulk, read the active session pointer
    session_dir = get_active_session_dir()
    if not session_dir:
        print("\n✖ Error: No active campaign session found!")
        print("Please initialize a new batch first: python3 run_campaign.py --mode init")
        print("This creates a timestamped folder and writes the pointer file.\n")
        sys.exit(1)
        
    state = load_session_state(session_dir)

    # Handle feedback administration
    if args.clear_feedback:
        clear_feedback_history(session_dir, state)
        sys.exit(0)
        
    if args.show_feedback:
        show_feedback_history(state)
        sys.exit(0)
        
    if args.feedback:
        state["accumulated_feedback"].append(args.feedback)
        save_session_state(session_dir, state)
        print(f"✔ Appended new design guideline: \"{args.feedback}\"")
        show_feedback_history(state)

    # Core Execution Loop
    print("\n" + "="*50)
    print(f"RUNNING ELVITY CAMPAIGN ENGINE (Mode: {args.mode.upper()})")
    print(f"Targeting Session Directory: {session_dir}")
    print(f"Loading system instructions: {os.path.join(ROOT_DIR, 'system.md')}")
    
    leads_to_process = generate_leads_batch(args.leads_csv, args.count, args.mode)
    print(f"Total leads selected for execution: {len(leads_to_process)}")
    
    # Assembly of Dynamic System Prompt (Loaded from Root):
    system_md_path = os.path.join(ROOT_DIR, "system.md")
    with open(system_md_path, "r", encoding="utf-8") as f:
        system_instructions = f.read()
        
    if state["accumulated_feedback"]:
        system_instructions += "\n\n=== CRITICAL USER DESIGN AMENDMENTS (ACCUMULATED HISTORICAL FEEDBACK) ===\n"
        for i, fb in enumerate(state["accumulated_feedback"], 1):
            system_instructions += f"[{i}] {fb}\n"

    # Prepare master campaign CSV file inside the session folder
    outbound_csv_path = os.path.join(session_dir, "outbound_campaign.csv")
    csv_exists = os.path.exists(outbound_csv_path)
    
    csv_file = open(outbound_csv_path, "a" if csv_exists else "w", newline="", encoding="utf-8")
    fieldnames = [
        "Company", "Website", "Role", "First Name", "Last Name",
        "subject1", "message1", "subject2", "message2", "subject3", "message3",
        "compiled_html_path", "hosted_live_url"
    ]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    if not csv_exists:
        writer.writeheader()

    print("\nStarting Lead Generation, Config Drafting, Template Ingestion, and S3 Deployment loop...\n")
    
    for idx, lead in enumerate(leads_to_process, 1):
        company_name = lead.get("Company Name", "Unknown")
        website = lead.get("Website", "Unknown")
        print(f"[{idx}/{len(leads_to_process)}] Processing Lead: {company_name}...")
        
        # Call the programmatic Icon Resolver to download and convert the favicon
        download_and_convert_favicon(session_dir, company_name, website)
        
        # Call Gemini to generate the personalized config JSON
        campaign_json = run_gemini_inference(lead, system_instructions)
        if not campaign_json:
            print(f"   ✖ Warning: Failed to generate campaign context for {company_name}. Skipping.")
            continue
            
        # Ensure partner_icon_path is correct in JSON (points to session directory relatively)
        company_clean = company_name.lower().replace(" ", "_")
        campaign_json["partner_icon_path"] = f"./{company_clean}_icon.png"
        
        # Save config JSON inside the session folder
        config_path = os.path.join(session_dir, f"{company_clean}_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(campaign_json, f, indent=2)
            
        # Programmatically execute compile_onboarder.py on the config
        html_path = compile_lead_html(session_dir, company_name, config_path)
        if not html_path:
            print(f"   ✖ Warning: Failed to compile HTML page for {company_name}.")
            continue
            
        # Deploy compiled HTML and icons directly to S3 Bucket
        # STRICT COMPLIANCE: If this fails, program aborts/terminates execution immediately.
        hosted_url = upload_assets_to_s3(session_dir, company_name, html_path)
        
        # Weave the live, hosted public URL directly into message1
        msg1_copy = campaign_json.get("message1", "")
        msg1_copy_woven = msg1_copy.replace("{{DEMO_URL}}", hosted_url)
        
        # Write outputs directly into the master CSV inside the session folder
        writer.writerow({
            "Company": company_name,
            "Website": lead.get("Website", ""),
            "Role": lead.get("Title", ""),
            "First Name": lead.get("First Name", ""),
            "Last Name": lead.get("Last Name", ""),
            "subject1": campaign_json.get("subject1", ""),
            "message1": msg1_copy_woven,
            "subject2": campaign_json.get("subject2", ""),
            "message2": campaign_json.get("message2", ""),
            "subject3": campaign_json.get("subject3", ""),
            "message3": campaign_json.get("message3", ""),
            "compiled_html_path": html_path,
            "hosted_live_url": hosted_url
        })
        csv_file.flush() # Ensure it's immediately written to disk
        
        # Subtle sleep to prevent rapid API rate limits (backoff)
        time.sleep(1)
        
    csv_file.close()
    
    # Update state
    state["status"] = "sampling" if args.mode == "sample" else "completed"
    save_session_state(session_dir, state)
    
    print("\n" + "="*50)
    print("CAMPAIGN RUN COMPLETED SUCCESSFULLY!")
    print(f"Master Outbound Copy saved to: {outbound_csv_path}")
    print(f"Personalized HTML pages saved and uploaded successfully!")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
