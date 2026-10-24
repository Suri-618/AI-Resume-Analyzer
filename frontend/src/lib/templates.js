// Resume templates. The definitions live in resumeTemplates.json, an exact copy of
// app/data/resume_templates.json (a backend test checks they match), so the
// preview and the downloaded .docx always agree.
import data from './resumeTemplates.json';

export const TEMPLATES = data.templates;
export const FONTS = data.fonts;
export const ORDERS = data.orders;
export const DEFAULT_TEMPLATE = 'tech-classic';

export const templateById = (id) => TEMPLATES.find((t) => t.id === id) || TEMPLATES.find((t) => t.id === DEFAULT_TEMPLATE);

// Page margin, space before a heading and after a paragraph, in points (same as the .docx)
export const DENSITY = {
  compact: { margin: 36, before: 7, after: 1 },
  normal: { margin: 48, before: 10, after: 2 },
  airy: { margin: 56, before: 14, after: 3 },
};

let fontsRequested = false;
/** Load the web versions of the template fonts (metric-compatible with Calibri, Cambria, Arial…) once. */
export function loadTemplateFonts() {
  if (fontsRequested || typeof document === 'undefined') return;
  fontsRequested = true;
  const families = Object.values(FONTS)
    .map((f) => `family=${f.google}`)
    .join('&');
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = `https://fonts.googleapis.com/css2?${families}&display=swap`;
  document.head.appendChild(link);
}

/** A sample resume for template thumbnails and "start from a sample": a full one-page student resume. */
export const SAMPLE_RESUME = {
  name: 'Gadde Vardhan Sai',
  headline: 'Computer Science (AI & ML) Student | Aspiring Full-Stack Developer',
  email: 'gadde.vardhansai@email.com',
  phone: '+91 98765 43210',
  location: 'Bengaluru, India',
  links: ['github.com/gaddevardhansai', 'linkedin.com/in/gaddevardhansai'],
  summary:
    'Final-year B.Tech student who builds and ships full-stack and machine learning apps. Comfortable across React, FastAPI, Python and SQL, with an internship building internal tools used by 200+ employees.',
  skills: [
    'Languages: Python',
    'JavaScript',
    'TypeScript',
    'SQL',
    'Java',
    'Web: React',
    'Node.js',
    'FastAPI',
    'REST APIs',
    'Tailwind CSS',
    'Data & ML: scikit-learn',
    'pandas',
    'NumPy',
    'NLP',
    'Tools: Git',
    'Docker',
    'PostgreSQL',
    'Linux',
    'GitHub Actions',
  ],
  experience: [
    {
      title: 'Software Engineering Intern, Acme Technologies',
      subtitle: 'Bengaluru, India',
      date: 'May 2025 – Jul 2025',
      link: '',
      bullets: [
        'Built an internal leave-management tool in React and Node.js used by 200+ employees.',
        'Cut API response time by 35% by adding PostgreSQL indexes and caching hot queries.',
        'Wrote 60+ unit and integration tests and set up CI that runs on every pull request.',
      ],
    },
  ],
  projects: [
    {
      title: 'FitLens – AI Resume Analyzer',
      subtitle: 'Python, FastAPI, scikit-learn, React, Supabase',
      date: '2026',
      link: 'github.com/gaddevardhansai/fitlens',
      bullets: [
        'Trained a Ridge regression match scorer (R² 0.38 on unseen jobs) and a Linear SVM role classifier (92% top-3 accuracy, 24 categories).',
        'Built ATS checks, a resume builder with 15 templates and live job search; deployed with 250+ automated tests.',
      ],
    },
    {
      title: 'Campus Events Platform',
      subtitle: 'React, Node.js, PostgreSQL',
      date: '2025',
      link: 'github.com/gaddevardhansai/events',
      bullets: [
        'Built a full-stack app for event sign-ups, used by 1,200+ students in its first semester.',
        'Added email reminders and a waitlist that filled 95% of cancelled seats.',
      ],
    },
    {
      title: 'Expense Tracker API',
      subtitle: 'Python, FastAPI, Docker',
      date: '2024',
      link: 'github.com/gaddevardhansai/expense-api',
      bullets: ['Designed a REST API with JWT auth and monthly reports, containerised with Docker.'],
    },
  ],
  education: [
    {
      title: 'B.Tech in Computer Science and Engineering (AI & ML)',
      subtitle: 'National Institute of Technology · CGPA 8.7/10',
      date: '2022 – 2026',
      link: '',
      bullets: [],
    },
  ],
  certifications: [
    '[AWS Certified Cloud Practitioner](https://aws.amazon.com/certification/certified-cloud-practitioner/)',
    'Meta Front-End Developer (Coursera)',
  ],
  achievements: ['Winner, Smart India Hackathon 2024 (software edition)', 'Solved 400+ problems on LeetCode'],
  additional: [{ heading: 'Languages', items: ['English, Hindi, Kannada'] }],
};

export const EMPTY_RESUME = {
  name: '',
  headline: '',
  email: '',
  phone: '',
  location: '',
  links: [],
  summary: '',
  skills: [],
  experience: [],
  projects: [],
  education: [],
  certifications: [],
  achievements: [],
  additional: [],
};
