# FitLens — Technical Guide

> How every part of FitLens works, the data and model results in detail, the API, and how to run, retrain and deploy it. For the project overview, see the [README](../README.md).

[![CI](https://github.com/Suri-618/AI-Resume-Analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/Suri-618/AI-Resume-Analyzer/actions/workflows/ci.yml)

**Live application:** https://ai-resume-analyzer-plus.vercel.app/  
**Backend API:** https://ai-resume-analyzer-api-9709.onrender.com/  
**GitHub repository:** https://github.com/Suri-618/AI-Resume-Analyzer

A free career toolkit for students and freshers. The home page is a dashboard of four tools:

| Tool | Route | What it does |
|---|---|---|
| **Check my resume** | `/check` | Upload a resume (PDF or DOCX), optionally with a job description, for the analysis report. |
| **Build a resume** | `/build` | 15 ATS-friendly templates, live preview, import from an existing resume, PDF and Word downloads, and resume score checking. Drafts are saved in the browser. |
| **Find jobs & internships** | `/jobs` | Live openings, matching scores, requested skills, and prefilled searches on job platforms. |
| **Learn a skill** | `/learn` | Choose skills or a career path and get a study roadmap with resources, checklists, schedules, and projects. |

Signing in is optional (Google or an email link, via Supabase). With an account, supported data such as resumes, roadmap progress, and the application tracker (`/tracker`: Saved → Applied → Interview → Offer) can be saved across devices. Without an account, the application remains usable and drafts stay in the browser.

The resume report has five tabs:

| Tab | What you get |
|---|---|
| **Overview** | Match score (0–100) when a job description is supplied, explanation of the score, posting insights, resume strength, target-role gap, job categories, extracted skills, and GitHub proof check. |
| **ATS check** | A 0–100 estimate of ATS compatibility, covering layout, sections, contact details, bullets, and keywords. Student mode adds a fresher checklist. |
| **Edit & re-check** | Editable resume sections, bullet coach feedback, one-click re-check, and ATS-friendly DOCX download. |
| **Skill plan** | Portfolio project recommendations and a learning roadmap for missing skills, including prerequisites, learning resources, estimated hours, checklists, and project ideas. |
| **Find jobs** | Live jobs and internships, fit scores, matched and missing skills, application links, and skill-demand insights. |

---

## How it works

```text
Browser (React, Vercel)
  │
  │ POST /api/analyze
  │ multipart: resume_file + job_description
  ▼
FastAPI on Render (Docker)
  │
  ├── app/main.py
  │     CORS, request body limit, rate limiting
  │
  ├── app/routers/analyze.py
  │     /analyze, /recheck, /resume/docx, /suggest-roles
  │
  └── app/services/pipeline.py
        File validation and analysis orchestration
        │
        ├── parser.py
        │     PDF/DOCX parsing and layout extraction
        │
        ├── data_cleaning.py
        │     Training-data normalization
        │
        ├── skill_extractor.py
        │     436-skill taxonomy and aliases
        │
        ├── matcher.py
        │     TF-IDF features → Ridge Regression → match score
        │
        ├── suggestions.py
        │     Rule-based improvement suggestions
        │
        ├── role_predictor.py
        │     TF-IDF → calibrated LinearSVC
        │
        ├── resume_sections.py
        │     Editable resume sections
        │
        ├── ats_checker.py
        │     ATS compatibility checks
        │
        ├── job_decoder.py
        │     Job requirements and experience extraction
        │
        ├── learning_plan.py
        │     Missing skills → learning resources
        │
        ├── role_gap.py
        │     Resume vs target-role comparison
        │
        ├── skills_inventory.py
        │     Extracted skills and groups
        │
        └── resume_docx.py
              ATS-friendly Word document generation

Frontend integrations:
  ├── Supabase Auth and PostgreSQL
  ├── GitHub public API
  └── External job APIs
```

### Match score

The match scorer uses Ridge Regression on three features that can all be computed at inference time:

| Feature | Meaning | Approximate effect |
|---|---|---|
| `tfidf_similarity` | TF-IDF cosine similarity between resume and job text | +1.3 points per +0.01 similarity |
| `skill_overlap_ratio` | Share of job skills found in the resume | +4.8 points per +10% of required skills |
| `resume_word_count` | Resume length | +0.7 points per +100 words |

Because the model is linear, the API also returns `score_breakdown`: a baseline plus each feature's signed contribution. The UI displays this as "Why this score".

Raw linear predictions can exceed 100. Instead of a hard clip, the score is soft-capped: unchanged between 15 and 85, smoothly compressed beyond those values, and ranking-preserving.

When the cap changes a score, the breakdown includes a `range_adjustment` line so the contributions still add up.

Resumes under 150 words or job descriptions under 50 words receive `score_warnings`, because they are outside the typical training-data range.

### Job categories

A TF-IDF word-and-bigram model with sublinear term frequency feeds a `CalibratedClassifierCV(LinearSVC)` classifier.

It was trained on 2,484 resumes across 24 industry categories.

If the top probability is low or the resume is short, predictions are blended with skill overlap against curated role profiles in `app/data/role_profiles.json`.

The response reports `"confidence": "low"` when the final top probability is below 50%.

### ATS check

`app/services/ats_checker.py` checks common issues that can affect applicant tracking systems.

The checks are weighted into a 0–100 estimate:

- Pass: full weight.
- Warn: half weight.
- Fail: zero weight.

| Area | Checks |
|---|---|
| Format and layout | Text extraction, tables, single-column layout, images, text boxes, contact details in headers/footers, page count |
| Content | Email, phone, LinkedIn/portfolio links, standard section headings, word count, bullets, numbers, action verbs, emoji/icon characters |
| Keywords | Share of the job's skills found in the resume |

This is a transparent heuristic, not the output of a real ATS.

Edited or pasted resumes are exported through a plain single-column DOCX template, so their layout checks count as passes.

### Edit & re-check

`resume_sections.py` splits extracted resume text into:

- Contact details
- Summary
- Skills
- Experience
- Projects
- Education
- Certifications
- Other sections

Headings, bullets, wrapped lines, and date lines are recognized.

The UI displays the sections in an editable form.

- **Re-check:** analyzes the edited resume using `POST /api/recheck`.
- **Download:** creates an ATS-friendly DOCX using `POST /api/resume/docx`.

The generated Word document uses one column, standard headings, real Word bullet lists, and no tables, images, or headers.

### Student features

- **Job decoder (`job_decoder.py`):** Reads job postings and identifies must-have skills, nice-to-have skills, experience requirements, job level, and degree requirements.
- **Learning plan (`learning_plan.py`):** Uses `app/data/learning_resources.json` to recommend resources for 75 common skills. It includes explanations, documentation, free courses, YouTube videos, project ideas, estimated hours, prerequisites, and checklists.
- **Project picker (`project_picker.py`):** Chooses one or two projects from 36 curated student-sized ideas. Projects are ranked according to the missing skills they cover.
- **Student mode:** Adds checks for education, projects, internships or training, grades, GitHub/portfolio links, and one-page resume length.
- **Bullet coach:** Runs in the browser using `frontend/src/lib/bulletCoach.js`.

### Resume-only mode

An empty job description gives `"mode": "resume_only"`.

In this mode:

- `match_score` is `null`.
- Job-specific fields are empty.
- ATS analysis, role predictions, role gaps, and skills inventory are still returned.
- A role-based learning plan is generated.

Target roles are stored in `app/data/target_roles.json`. They are separate from the classifier's 24 broad dataset categories to provide more useful career recommendations.

The resume strength report is computed in the browser using `frontend/src/lib/strength.js`.

### Resume generator

The resume generator is available through the builder at `/build?start=generate`.

It collects contact details, target role, education, projects, internships, and additional skills.

`POST /api/resume/generate` uses `app/services/resume_generator.py` to generate resume content without an external AI service.

Its main rules are:

- Weak bullet openers are replaced with more specific action verbs.
- Technical skills relevant to the target role are prioritized.
- Results and measurable achievements are highlighted when supplied.
- Summary and headline are based on the student's actual information.
- Only user-provided skills are included as confirmed skills.
- Missing job skills are returned as `suggested_skills`, not automatically claimed.
- Projects are ranked according to their relevance to the target role.
- The generator limits content to help keep the resume concise.
- Different wording variants change sentence patterns without changing facts.
- Leadership and activities can be included for students with limited work experience.

`POST /api/resume/project-ideas` recommends up to three curated project ideas for students who do not yet have projects.

### Resume builder

Templates are stored in `app/data/resume_templates.json` and mirrored in `frontend/src/lib/resumeTemplates.json`.

A test checks that both copies match.

Each template defines fonts, sizes, header alignment, heading styles, accent colours, section order, and spacing.

The same template definition drives:

- Browser preview (`ResumeDocument.jsx`).
- Browser print-to-PDF.
- Word document generation (`resume_docx.py`).

Every template is designed to remain ATS-friendly with one column and standard headings.

### Accounts (Supabase)

FitLens uses Supabase Auth for Google and email authentication and Supabase PostgreSQL for account-related data.

The frontend connects to Supabase using the public publishable/anon key. Never expose the service-role key in frontend code.

The database schema is stored in `supabase/schema.sql`.

It creates the supported application tables, including:

- `resumes`
- `learning_progress`
- `applications`

Row Level Security (RLS) policies restrict users to their own records.

The schema also defines a `delete_my_account()` function for account deletion.

#### Supabase project configuration

The current Supabase project URL is:

```text
https://trjqihichgkrnhtzlmlq.supabase.co
```

The Google OAuth callback URL is:

```text
https://trjqihichgkrnhtzlmlq.supabase.co/auth/v1/callback
```

To configure authentication:

1. Open your Supabase project.
2. Navigate to Authentication → URL Configuration.
3. Set the production Site URL:

   ```text
   https://ai-resume-analyzer-plus.vercel.app
   ```

4. Add the production redirect URL:

   ```text
   https://ai-resume-analyzer-plus.vercel.app/**
   ```

5. Add the local development redirect URL:

   ```text
   http://localhost:5173/**
   ```

6. Navigate to Authentication → Sign In / Providers → Google.
7. Enable Google authentication and configure the Google OAuth Client ID and Client Secret from the same Google Cloud OAuth Web application.
8. In Google Cloud Console, add this authorized redirect URI:

   ```text
   https://trjqihichgkrnhtzlmlq.supabase.co/auth/v1/callback
   ```

9. Add the production frontend origin to the Google OAuth authorized JavaScript origins:

   ```text
   https://ai-resume-analyzer-plus.vercel.app
   ```

10. Save the configuration.

#### Frontend environment variables

Set these in Vercel → Project → Settings → Environment Variables:

```env
VITE_SUPABASE_URL=https://trjqihichgkrnhtzlmlq.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
```

For local development, place the same variable names in `frontend/.env.local`.

Never commit `.env.local`, OAuth client secrets, or service-role keys.

After changing production environment variables, redeploy the frontend.

### GitHub proof check

The browser reads the student's public GitHub profile and repositories using GitHub's public API.

`POST /api/github-check` (`app/services/github_check.py`) compares repository information with resume skills.

Repository evidence can include:

- Programming languages.
- Repository topics.
- Repository names and descriptions.
- Technology-related project information.

Forks do not count as original project evidence.

The report identifies:

- Skills supported by public repositories.
- Skills without public repository evidence.
- Skills shown by repositories but missing from the resume.
- Suggested GitHub profile improvements.

### Live job search

`POST /api/jobs` (`app/services/job_search.py`) fetches current postings and scores them against the resume using the same match model.

Supported sources include:

- **Himalayas:** Remote job listings.
- **Adzuna:** Job listings in supported countries.

Adzuna requires optional developer credentials:

```env
ADZUNA_APP_ID=YOUR_ADZUNA_APP_ID
ADZUNA_APP_KEY=YOUR_ADZUNA_APP_KEY
```

These must be configured on the backend, not exposed in the frontend.

Job search results include fit scores, matched skills, missing skills, application URLs, and source information.

Results are cached to reduce unnecessary external API requests.

---

## Data

| File | Rows | Used for |
|---|---:|---|
| `data/raw/Resume.csv.gz` | 2,484 resumes, 24 categories | Role classifier |
| `data/raw/job_resume_fit.csv.gz` | 2,385 resume-job pairs, 23 unique job descriptions | Match scorer |

Data files are stored in compressed CSV format. Pandas can read `.csv.gz` files directly.

`data/processed/` contains generated datasets created by `scripts/build_processed_data.py`.

---

## Model performance

The following metrics are produced by the training scripts and stored in `reports/`.

### Match scorer

Evaluation uses GroupKFold with five folds grouped by job description. This prevents the same job description from appearing in both training and test folds.

| Model | R² | RMSE | MAE |
|---|---:|---:|---:|
| **Ridge (production)** | **0.377 ± 0.156** | **17.71 ± 2.14** | **14.48 ± 2.11** |
| Random Forest | 0.349 ± 0.174 | 18.13 ± 2.50 | 14.66 ± 2.69 |
| Gradient Boosting | 0.280 ± 0.127 | 19.29 ± 3.18 | 15.52 ± 3.20 |

Predictions are soft-capped using the same process as production.

### Role classifier

The classifier uses a stratified 80/20 split with 497 test resumes.

| Test set | Top-1 | Top-3 | Macro F1 |
|---|---:|---:|---:|
| Full resume, title kept | 73.2% | 92.2% | 0.688 |
| **Full resume, title removed** | **70.0%** | **89.5%** | **0.660** |
| 250-word snippet | 62.8% | 80.3% | 0.592 |
| 120-word snippet | 52.9% | 70.4% | 0.490 |

The title-removed result is more representative of real resumes, where the opening line usually contains a person's name rather than a job-category label.

### Short resumes and fallback

The skill-overlap fallback is used for short resumes or predictions with very low confidence.

On 19 hand-written student-style resumes, the raw model classified 12 correctly, while the fallback classified all 19 correctly.

These results come from a small synthetic test set and should not be treated as a guarantee of real-world accuracy.

---

## Limitations

- **Small, AI-labelled match dataset:** The match scorer uses 23 unique job descriptions. Target scores were generated by an AI model rather than recruiters.
- **Limited semantic understanding:** TF-IDF similarity may miss paraphrased experience and equivalent technical terminology.
- **Broad job categories:** The role classifier predicts 24 industry categories, not every individual job title.
- **Short student resumes:** The original dataset contains longer professional resumes, so short student resumes rely more on fallback logic.
- **Text-based files:** Scanned or image-only PDFs without a text layer may not be parsed correctly.
- **ATS score is an estimate:** The ATS checker uses transparent rules and heuristics, not a real employer's ATS software.
- **Job availability:** External job listings may be outdated, unavailable, or incomplete.

---

## Run locally

Requirements:

- Python 3.14.
- Node.js 20 or later.
- npm.
- Git.

### Backend

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation, if enabled:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

### Checks

Backend:

```bash
ruff check .
ruff format --check .
pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

---

## API

The main API endpoints include:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/analyze` | Analyze an uploaded resume against a job description |
| POST | `/api/recheck` | Re-analyze edited resume sections |
| POST | `/api/resume/parse` | Parse a resume into editable sections |
| POST | `/api/resume/docx` | Generate an ATS-friendly Word document |
| POST | `/api/resume/generate` | Generate a resume from user-provided information |
| POST | `/api/resume/project-ideas` | Recommend portfolio projects |
| POST | `/api/role-gap` | Compare resume skills with a target role |
| POST | `/api/learn` | Generate a learning roadmap |
| GET | `/api/learn/catalog` | List learning skills and career paths |
| POST | `/api/jobs` | Search for jobs and internships |
| GET | `/api/jobs/options` | Get supported job-search options |
| POST | `/api/github-check` | Compare resume skills with public GitHub repositories |
| POST | `/api/suggest-roles` | Suggest suitable job categories |
| GET | `/` | Backend health check |

### Analyze request

`POST /api/analyze`

Accepts multipart form data:

- `resume_file`: PDF or DOCX file, maximum 5 MB.
- `job_description`: Optional job description.
- `student_mode`: Optional student checklist setting.

It can also accept JSON:

```json
{
  "resume_text": "Resume text here",
  "job_text": "Job description here"
}
```

The response can include:

- `match_score`
- `score_breakdown`
- `features`
- `matched_skills`
- `missing_skills`
- `score_warnings`
- `suggestions`
- `suggested_roles`
- `confidence`
- `resume`
- `ats`
- `job_insights`
- `learning_plan`
- `project_picks`
- `student_mode`
- `student_detected`

### Re-check request

`POST /api/recheck`

```json
{
  "resume": {
    "summary": "Resume summary",
    "skills": ["Python", "SQL"]
  },
  "job_description": "Job description here",
  "student_mode": false
}
```

### Role-gap request

`POST /api/role-gap`

```json
{
  "resume": {
    "skills": ["Python", "SQL"]
  },
  "target_role": "Data Analyst"
}
```

### Job search request

`POST /api/jobs`

```json
{
  "resume": {
    "skills": ["Python", "SQL"]
  },
  "query": "Data Analyst",
  "country": "IN",
  "kind": "internship"
}
```

### Learning roadmap request

`POST /api/learn`

```json
{
  "skills": ["React", "Docker"],
  "known": ["HTML"]
}
```

### GitHub proof request

`POST /api/github-check`

Accepts the public GitHub profile and repository information.

### API errors

Errors are returned as JSON:

```json
{
  "detail": "Error description"
}
```

Possible status codes include:

- `400`: Invalid file or input.
- `413`: Request body exceeds the configured limit.
- `422`: Validation error.
- `429`: Rate limit exceeded.
- `503`: Required model files are missing.

For the exact implementation and response schemas, refer to `app/routers/` and `app/schemas/`.

---

## Retraining the models

The training scripts are located in `scripts/`.

```bash
python scripts/build_processed_data.py
python scripts/build_skills_taxonomy.py
python -m app.ml.features
python scripts/train_match_scorer.py
python scripts/train_role_classifier.py
python scripts/evaluate_pipeline.py
python scripts/build_learning_resources.py
python scripts/build_target_roles.py
```

The generated files are stored in `data/processed/`, `app/data/`, `models/`, and `reports/`.

`requirements.txt` pins the scikit-learn version used to serialize the models. If you upgrade scikit-learn, retrain the models before deploying.

---

## Deployment

### Frontend — Vercel

**Production URL:**

https://ai-resume-analyzer-plus.vercel.app/

The frontend is built using React and Vite and deployed on Vercel.

Important configuration:

- Root Directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`

Frontend environment variables:

```env
VITE_SUPABASE_URL=https://trjqihichgkrnhtzlmlq.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
```

If the frontend is configured to call the backend directly, configure:

```env
VITE_API_BASE_URL=https://ai-resume-analyzer-api-9709.onrender.com
```

If the project uses the Vercel `/api` rewrite instead, keep the API base URL configuration consistent with `frontend/vercel.json`.

After changing environment variables, redeploy the frontend.

### Backend — Render

**Production API URL:**

https://ai-resume-analyzer-api-9709.onrender.com/

The backend uses FastAPI and Docker and is deployed on Render.

The root health-check endpoint is:

```text
https://ai-resume-analyzer-api-9709.onrender.com/
```

Expected response:

```json
{
  "message": "Welcome to Resume Analyzer API",
  "status": "active"
}
```

Backend environment variables should be configured in the Render dashboard.

| Variable | Purpose |
|---|---|
| `CORS_ORIGINS` | Allowed frontend origins |
| `ENABLE_DOCS` | Enables or disables API documentation |
| `RATE_LIMIT_PER_MINUTE` | Configures API rate limiting |
| `LOG_LEVEL` | Backend logging level |
| `ADZUNA_APP_ID` | Optional Adzuna application ID |
| `ADZUNA_APP_KEY` | Optional Adzuna application key |

For production, ensure `CORS_ORIGINS` includes:

```text
https://ai-resume-analyzer-plus.vercel.app
```

Do not store private API credentials in frontend environment variables.

**Note:** Render free services may sleep after inactivity. The first request after sleeping can take longer while the service starts.

---

## Project structure

```text
AI-Resume-Analyzer/
│
├── app/
│   ├── routers/           API routes
│   ├── schemas/           Request and response schemas
│   ├── services/          Resume analysis and application services
│   ├── ml/                Machine learning features
│   └── data/              Skills, roles and learning resources
│
├── data/
│   ├── raw/               Original datasets
│   └── processed/         Processed datasets
│
├── models/                Trained ML models
├── scripts/               Data processing and training scripts
├── reports/               Model evaluation reports
├── notebooks/             Exploratory data analysis
├── tests/                 Backend automated tests
│
├── frontend/
│   ├── public/
│   └── src/
│
├── supabase/
│   └── schema.sql
│
├── .github/
│   └── workflows/         CI workflows
│
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Repository and deployment links

| Resource | Link |
|---|---|
| GitHub Repository | https://github.com/Suri-618/AI-Resume-Analyzer |
| Live Frontend | https://ai-resume-analyzer-plus.vercel.app/ |
| Backend API | https://ai-resume-analyzer-api-9709.onrender.com/ |
| Supabase Project | https://supabase.com/dashboard/project/trjqihichgkrnhtzlmlq |

---

**FitLens — Understand your resume. Improve your skills. Move closer to your dream career.**
