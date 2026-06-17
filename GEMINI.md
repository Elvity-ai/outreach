# Elvity B2B Sales Campaign Orchestrator Playbook
**Your Interactive, LLM-Powered Outbound Campaign Portal**

Welcome to Elvity's programmatic B2B Campaign Engine! This workspace is designed for the Sales and Customer Success teams to automatically research prospective B2B clients, write personalized three-message email sequences, and compile bespoke, dual-branded interactive onboarding web pages hosted publicly on AWS S3.

---

## 🏗️ Folder Architecture (Code vs. Data Separation)

To ensure this system remains fully reusable and scalable for any future lead batches, we separate our **global system software** from our **transient campaign outputs**:

*   **Permanent System Software (Project Root):**
    *   `run_campaign.py`: The state-driven main command line and API orchestrator.
    *   `compile_onboarder.py`: The HTML template compiler.
    *   `elvity_onboarding_template.html`: The master light-mode HTML onboarding template.
    *   `system.md`: The single source of truth for messaging guidelines, tone constraints, and uploader table structures.
*   **Transient Campaign Outputs (Sessions Folder):**
    Each time you run a campaign, all intermediate data and compiled files are saved inside a dedicated, timestamped folder: `sessions/YYYY-MM-DD-HHMM/` (e.g. `session_state.json`, `pylon_config.json`, `pylon_demo.html`, `outbound_campaign.csv`).

---

## 🚀 Your Step-by-Step Campaign Workflow (Walkthrough)

When you start a session with me (Gemini CLI), we will walk through these **four interactive phases** together. You don't need to touch a terminal or write any code—just talk to me in natural language!

### 🟢 Step 1: Session Initialization
*   **What to tell me:** *"Hey, let's start a new campaign batch."*
*   **What happens under the hood:** I will execute `python3 run_campaign.py --mode init` from the root. This generates a new timestamped folder inside `sessions/`, writes an initial `session_state.json` ledger, and saves the active workspace path to `.active_session` in the root.
*   **Success Response:** I will confirm: *"New campaign session successfully initialized at `sessions/YYYY-MM-DD-HHMM/`!"*

### 🧪 Step 2: Sampling and Preview
*   **What to tell me:** *"Generate 4 sample leads."*
*   **What happens under the hood:** I will execute `python3 run_campaign.py --mode sample --count 4`. The script reads the first 4 leads from `new_leads.csv`, queries Gemini using our `system.md` instructions to draft their emails and custom tables, and compiles their custom onboarding pages locally in the session directory.
    *   **S3 Ingestion:** The script programmatically uploads the HTML pages and custom company favicons directly to our S3 public assets bucket (`s3://elvity-public-assets/viz/`).
    *   **Link Weaving:** The script programmatically replaces the `{{DEMO_URL}}` placeholder inside `message1` with the live, public S3 URL (e.g., `https://elvity-public-assets.s3.amazonaws.com/viz/pylon_demo.html`).
*   **Deliverables:** I will present the draft email copy sequences and their corresponding public demo URLs directly in our chat for your review.

### 🗣️ Step 3: Conversational Refinement (No-Amnesia Feedback Loop)
This is where we perfect the copy! Open the compiled `.html` files in your browser locally or click the public S3 links to inspect the visual layouts and looping animations.
*   **What to tell me:** Give me your feedback directly in chat:
    *   *"The tone for Relcu is too aggressive, let's make it more consultative."*
    *   *"Change Scowtt's primary color theme from hot pink to adtech blue."*
    *   *"Make sure all first emails are under 120 words."*
*   **What happens under the hood:** I will execute `python3 run_campaign.py --mode sample --feedback "[Your Correction]"`. The script appends your instructions directly to `session_state.json`. Because we maintain this cumulative state ledger, **I will never forget previous corrections.** I re-run the compiler with all historical constraints active and re-upload the updated pages.
*   **Deliverables:** I will show you the updated emails and prompt you to refresh your browser to see the styled web page updates instantly!

### 🚦 Step 4: Bulk Execution
Once you are 100% satisfied with the samples, we scale it to the rest of the list!
*   **What to tell me:** *"Go ahead"* or *"Satisfied"* or *"Proceed with bulk run."*
*   **What happens under the hood:**
    1.  I will write a streamlined Python bulk runner containing our approved prompt guidelines and accumulated feedback rules.
    2.  I will spin up the **Generalist Sub-Agent** to execute `python3 run_campaign.py --mode bulk` as a background thread.
    3.  The sub-agent loops through the remaining 390+ leads, compiling and uploading all 390+ HTML landing pages directly to S3 and appending their personalized outbound emails to `sessions/[active_session]/outbound_campaign.csv`.
*   **Deliverables:** I will monitor the background execution log and report back with a condensed execution summary once the entire bulk campaign is complete and ready to send!
