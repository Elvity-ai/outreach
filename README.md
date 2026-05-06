# Elvity B2B Sales Prospecting

This repository is used by the Elvity Sales team to research leads and generate high-conversion, personalized outreach messages.

## Core Product (Elvity)
Elvity is an embeddable data ingestion portal for B2B SaaS. It handles structured (CSV, Excel) and unstructured (PDFs, Invoices, Images) data, automating validation and "fix-up" to accelerate time-to-value for customers and increase engineering velocity.
Website: [www.elvity.ai](http://www.elvity.ai)

## Project Structure
- `GEMINI.md`: Contains the system prompts, messaging guidelines, and workflow instructions for the AI analyst.
- `leads.csv`: The input list of leads to be processed.
- `sessions/`: (Gitignored) Contains all generated outreach messages, samples, and final output CSVs, organized by timestamped session folders.

## Workflow
1. **Input:** Provide a CSV of leads in the root directory.
2. **Phase 1 (Sampling):** The AI selects 4-5 representative leads and generates 3 message variants (Implementation, Engineering, Unstructured Data) for review.
3. **Phase 2 (Refinement):** Feedback is provided on tone, use cases, and length.
4. **Phase 3 (Bulk Execution):** Once approved, the full list is processed and saved as a new CSV within a timestamped folder in `sessions/`.

## Messaging Tone
Messages should be written from the perspective of an **SF-based tech founder**. The tone is objective and non-definitive, focusing on seeking feedback and design partners ("no selling") rather than a direct sales pitch.
