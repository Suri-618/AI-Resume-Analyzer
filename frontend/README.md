# FitLens Frontend

React 19 + Vite + Tailwind CSS 4 single-page application for **FitLens — AI Resume Analyzer**.

Upload a resume (PDF/DOCX), with or without a job description, to get:

- Resume-to-job match score with a per-factor breakdown.
- Job description analysis and skill requirements.
- ATS compatibility check with a student/fresher checklist.
- Skill-gap analysis and personalized learning roadmap.
- Resume editor with a live bullet coach.
- ATS-friendly DOCX resume download.
- Live jobs and internships with individual fit scores.
- GitHub profile and repository skill verification.
- Resume builder with 15 professional templates.
- Optional accounts, saved resumes, learning progress, and application tracking.

**Live application:** https://ai-resume-analyzer-plus.vercel.app/  
**GitHub repository:** https://github.com/Suri-618/AI-Resume-Analyzer

---

## Design

FitLens uses a **paper & highlighter** design theme:

- Warm paper surfaces.
- Ink-colored text.
- Ink-blue primary accent.
- Highlighter yellow for matched skills.
- Red pen styling for missing skills and improvement areas.
- Fraunces for headings.
- Inter for body text.
- JetBrains Mono for numbers and technical labels.

Light and dark themes follow the system setting until the user selects a theme. The selected preference is saved in `localStorage`.

### Motion and interactions

Framer Motion provides small, purposeful animations:

- Matched skills receive a highlighter swipe.
- Missing skills receive a hand-drawn red underline.
- ATS scores animate like a rubber stamp.
- Active tabs use a spring-animated highlighter stroke.
- Scores count up when displayed.
- Page transitions and interactive elements use subtle animations.

All animations respect the operating system's reduced-motion preference through:

```jsx
<MotionConfig reducedMotion="user">
```

---

## Run locally

### Prerequisites

- Node.js 20 or later.
- npm.
- Python 3.14 for the backend.
- Git.

### 1. Install frontend dependencies

From the repository root:

```powershell
cd frontend
npm install
```

### 2. Start the backend

Open another terminal from the repository root:

```powershell
.venv\Scripts\activate
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

### 3. Start the frontend

From the `frontend` directory:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:5173
```

The Vite development server proxies `/api/*` requests to `http://127.0.0.1:8000` through `vite.config.js`.

### Available scripts

| Command | Description |
|---|---|
| `npm install` | Install dependencies |
| `npm run dev` | Start the development server |
| `npm run build` | Create the production build in `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run Oxlint |

---

## Environment variables

The frontend uses environment variables for API communication and optional Supabase authentication.

Create a `.env.local` file inside the `frontend` directory.

```env
# Backend API
VITE_API_BASE_URL=http://127.0.0.1:8000

# Supabase authentication
VITE_SUPABASE_URL=YOUR_SUPABASE_PROJECT_URL
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
```

For local development, the API base URL can also be left unset because Vite proxies `/api/*` requests to the local backend.

### Production configuration

The production frontend is deployed on Vercel.

**Frontend URL:**

```text
https://ai-resume-analyzer-plus.vercel.app/
```

**Backend URL:**

```text
https://ai-resume-analyzer-api-9709.onrender.com/
```

Configure the following environment variables in:

Vercel → Project → Settings → Environment Variables

```env
VITE_API_BASE_URL=https://ai-resume-analyzer-api-9709.onrender.com
VITE_SUPABASE_URL=https://trjqihichgkrnhtzlmlq.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY
```

After modifying environment variables, redeploy the Vercel application.

**Security notes:**

- Never expose Supabase service-role keys in frontend code.
- Never commit `.env.local` or other files containing private credentials.
- The Supabase publishable/anon key is intended for frontend use with correctly configured database security policies.
- Google OAuth Client Secrets must remain in Supabase provider configuration, not in frontend environment variables.

---

## How it talks to the API

The API wrapper is located at:

```text
src/lib/api.js
```

It calls the backend using the configured `VITE_API_BASE_URL` and a 120-second timeout. The longer timeout allows the Render free service to start after inactivity.

| Feature | Endpoint | Description |
|---|---|---|
| Analyze resume | `POST /api/analyze` | Upload PDF/DOCX and optionally provide a job description |
| Re-check resume | `POST /api/recheck` | Analyze edited resume sections |
| Change target role | `POST /api/role-gap` | Compare resume skills against a target role |
| Download resume | `POST /api/resume/docx` | Generate an ATS-friendly Word document |
| Find jobs | `POST /api/jobs` | Search jobs and internships |
| Job options | `GET /api/jobs/options` | Retrieve job search options |
| GitHub proof check | `POST /api/github-check` | Compare resume skills with GitHub repository information |
| Parse resume | `POST /api/resume/parse` | Extract editable resume sections |
| Generate resume | `POST /api/resume/generate` | Generate a resume using user-provided information |
| Project ideas | `POST /api/resume/project-ideas` | Recommend portfolio projects |
| Learning roadmap | `POST /api/learn` | Generate a learning plan |

### API request flow

```text
React Frontend
      |
      | Axios / HTTP
      |
      v
VITE_API_BASE_URL
      |
      v
FastAPI Backend (Render)
      |
      ├── Resume Parser
      ├── Skill Extractor
      ├── ML Match Scorer
      ├── Job Role Classifier
      ├── ATS Checker
      ├── Learning Plan
      └── Job Search
      |
      v
JSON Response
      |
      v
React Results Components
```

### Environment-specific API routing

| Environment | API configuration | Request destination |
|---|---|---|
| Local development | `VITE_API_BASE_URL` unset | Vite proxy → `http://127.0.0.1:8000` |
| Local development | `VITE_API_BASE_URL=http://127.0.0.1:8000` | Local FastAPI backend |
| Vercel production | Render backend URL configured | Render backend directly |
| Vercel production | API base URL unset | Vercel `/api/*` rewrite → Render backend |

The Vercel rewrite is configured in `frontend/vercel.json`.

---

## Supabase authentication

FitLens supports optional authentication through Supabase.

Supported sign-in methods include:

- Google Sign-In.
- Email authentication.

The Supabase client is initialized in:

```text
src/lib/supabase.js
```

The authentication context is managed through:

```text
src/lib/authContext.js
```

The frontend uses Supabase Auth directly.

### Current Supabase project

```text
Project URL:
https://trjqihichgkrnhtzlmlq.supabase.co

Google OAuth callback:
https://trjqihichgkrnhtzlmlq.supabase.co/auth/v1/callback
```

### Authentication configuration

In Supabase:

1. Open Authentication → URL Configuration.
2. Set the production Site URL:

   ```text
   https://ai-resume-analyzer-plus.vercel.app
   ```

3. Add the production redirect URL:

   ```text
   https://ai-resume-analyzer-plus.vercel.app/**
   ```

4. Add the local redirect URL:

   ```text
   http://localhost:5173/**
   ```

5. Open Authentication → Sign In / Providers → Google.
6. Ensure Google authentication is enabled and configured with the correct Google OAuth Client ID and Client Secret.
7. In Google Cloud Console, configure the Supabase callback URL as an authorized redirect URI.

If Supabase environment variables are not configured, the Sign In button is hidden and the remaining frontend features continue to work.

---

## Demo mode

FitLens includes demo data so users can explore the results interface without running the backend.

Available demo routes:

| URL | Description |
|---|---|
| `/?demo=high` | High resume match example |
| `/?demo=low` | Low resume match example |
| `/?demo=resume` | Resume-only analysis without a job description |

Demo payloads are defined in:

```text
src/lib/demo.js
```

They follow the same general response structure as the real analysis API.

---

## Frontend structure

```text
frontend/
│
├── public/
│
├── src/
│   ├── App.jsx
│   │
│   ├── main.jsx
│   ├── index.css
│   │
│   ├── lib/
│   │   ├── api.js
│   │   ├── bulletCoach.js
│   │   ├── templates.js
│   │   ├── jobSites.js
│   │   ├── storage.js
│   │   ├── supabase.js
│   │   ├── authContext.js
│   │   ├── cloud.js
│   │   ├── tools.js
│   │   ├── demo.js
│   │   ├── sampleJobs.js
│   │   ├── strength.js
│   │   ├── motion.js
│   │   └── resume.js
│   │
│   ├── hooks/
│   │
│   ├── utils/
│   │   └── format.js
│   │
│   └── components/
│       ├── layout/
│       ├── auth/
│       ├── pages/
│       ├── resume/
│       ├── ui/
│       ├── upload/
│       ├── results/
│       │   ├── ResultsView.jsx
│       │   ├── SummaryCards.jsx
│       │   ├── OverviewTab.jsx
│       │   ├── AtsTab.jsx
│       │   ├── EditTab.jsx
│       │   ├── LearnTab.jsx
│       │   ├── ProjectPicks.jsx
│       │   ├── JobsTab.jsx
│       │   ├── overview/
│       │   └── edit/
│       │
│       ├── AnalyzingView.jsx
│       └── ErrorBoundary.jsx
│
├── .env.example
├── index.html
├── package.json
├── vite.config.js
├── vercel.json
└── README.md
```

### Important modules

| Module | Responsibility |
|---|---|
| `lib/api.js` | API requests, timeout handling, errors, DOCX downloads and GitHub integration |
| `lib/bulletCoach.js` | Instant rule-based feedback on resume bullets |
| `lib/templates.js` | Resume templates, fonts and sample resume |
| `lib/storage.js` | Browser storage for drafts and roadmap progress |
| `lib/supabase.js` | Supabase client initialization |
| `lib/authContext.js` | Authentication state and `useAuth()` |
| `lib/cloud.js` | Saved resumes, learning progress and applications |
| `lib/demo.js` | Demo analysis payloads |
| `lib/strength.js` | Resume strength grades |
| `lib/motion.js` | Shared animation presets |
| `hooks/` | Reusable React hooks |
| `components/results/` | Resume analysis results and tabs |
| `components/resume/` | Resume editor, templates and document rendering |

---

## Deployment — Vercel

The frontend is deployed using Vercel.

**Production URL:**

https://ai-resume-analyzer-plus.vercel.app/

### Vercel project configuration

| Setting | Value |
|---|---|
| Framework | Vite |
| Root Directory | `frontend` |
| Install Command | `npm install` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

The Vercel project uses:

```text
frontend/vercel.json
```

This configuration supports:

- Vite production builds.
- `/api/*` rewrites to the Render backend.
- SPA fallback to `index.html` for client-side routes.

### Backend connection

The production backend is:

https://ai-resume-analyzer-api-9709.onrender.com/

When using direct API requests, configure `VITE_API_BASE_URL` in Vercel and ensure the backend allows the frontend origin through its CORS configuration.

If using the Vercel rewrite, keep `VITE_API_BASE_URL` unset so requests use the configured `/api/*` rewrite.

---

## Development notes

- Keep API calls inside `src/lib/api.js` instead of duplicating request logic in components.
- Use reusable components for consistent UI.
- Keep demo response structures aligned with the backend API.
- Store only non-sensitive preferences and drafts in browser storage.
- Keep authentication and database access behind Supabase Auth and RLS.
- Follow the reduced-motion preference for animations.
- Run the production build before committing frontend changes.

### Production build

```bash
npm run lint
npm run build
```

The generated production bundle is stored in:

```text
dist/
```

---

## Related documentation

- [Main Project README](../README.md)
- [Technical Guide](../docs/TECHNICAL.md)
- [GitHub Repository](https://github.com/Suri-618/AI-Resume-Analyzer)
- [Live FitLens Application](https://ai-resume-analyzer-plus.vercel.app/)

---

**FitLens — Understand your resume. Improve your skills. Move closer to your dream career.**
