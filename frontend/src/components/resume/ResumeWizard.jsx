import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Sparkles, X } from 'lucide-react';
import { useEffect, useId, useState } from 'react';
import { fetchLearnCatalog, generateResume } from '../../lib/api';
import { useAuth } from '../../lib/authContext';
import { emptyWizardItem, snapshot } from '../../lib/resume';
import { KEYS, readStorage, writeStorage } from '../../lib/storage';
import { LineList, TagInput, TextField } from '../results/edit/fields';
import Button from '../ui/Button';
import WizardItems from './WizardItems';
import WizardResult from './WizardResult';

const STEPS = ['About you', 'Your goal', 'Education', 'Projects & internships', 'Skills & extras'];

const EMPTY = {
  name: '',
  email: '',
  phone: '',
  location: '',
  github: '',
  linkedin: '',
  target_role: '',
  job_description: '',
  education: { degree: 'B.Tech', branch: '', school: '', start: '', end: '', grade: '' },
  items: [],
  skills: [],
  certifications: [],
  achievements: [],
};

/** The answers in the shape the /api/resume/generate endpoint expects. */
function toRequest(answers, variant) {
  const { github, linkedin, education, items, ...rest } = answers;
  return {
    ...rest,
    links: [github, linkedin].map((l) => l.trim()).filter(Boolean),
    education: [education],
    items: JSON.parse(snapshot(items)),
    variant,
  };
}

function Step({ title, hint, children }) {
  return (
    <motion.section key={title} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} className="card p-5 sm:p-6">
      <h2 className="font-display text-2xl font-semibold">{title}</h2>
      {hint && <p className="mt-1 mb-5 text-sm text-muted">{hint}</p>}
      {children}
    </motion.section>
  );
}

function RoleField({ value, onChange }) {
  const id = useId();
  const [roles, setRoles] = useState([]);
  useEffect(() => {
    let live = true;
    fetchLearnCatalog()
      .then((c) => live && setRoles((c.roles || []).map((r) => r.role)))
      .catch(() => {}); // free text still works without the list
    return () => {
      live = false;
    };
  }, []);
  return (
    <div>
      <label htmlFor={id} className="label">
        Target role
      </label>
      <input
        id={id}
        list={`${id}-roles`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Software Engineer, Data Analyst…"
        className="field"
      />
      <datalist id={`${id}-roles`}>
        {roles.map((r) => (
          <option key={r} value={r} />
        ))}
      </datalist>
    </div>
  );
}

/** Answer a few questions; FitLens writes the whole resume (rule-based, no AI service). */
export default function ResumeWizard({ onCancel, onUse, notify }) {
  const { user } = useAuth();
  const [answers, setAnswers] = useState(() => {
    const saved = readStorage(KEYS.wizard);
    const base = { ...EMPTY, ...saved, education: { ...EMPTY.education, ...saved?.education } };
    base.items = base.items?.length ? base.items.map((i) => ({ ...emptyWizardItem(i.kind), ...i })) : [emptyWizardItem()];
    if (!base.name && user) base.name = user.user_metadata?.full_name || user.user_metadata?.name || '';
    if (!base.email && user) base.email = user.email || '';
    return base;
  });
  const [step, setStep] = useState(0);
  const [result, setResult] = useState(null);
  const [variant, setVariant] = useState(0);
  const [busy, setBusy] = useState(false);

  // Answers are kept in this browser, so a refresh doesn't lose them
  useEffect(() => {
    const id = setTimeout(() => writeStorage(KEYS.wizard, JSON.parse(snapshot(answers))), 400);
    return () => clearTimeout(id);
  }, [answers]);

  const set = (key) => (value) => setAnswers((a) => ({ ...a, [key]: value }));
  const setEdu = (key) => (value) => setAnswers((a) => ({ ...a, education: { ...a.education, [key]: value } }));
  const ready = answers.name.trim() && answers.items.some((i) => i.title.trim() || i.what.trim());

  const generate = async (nextVariant = variant, nextAnswers = answers) => {
    setBusy(true);
    try {
      setResult(await generateResume(toRequest(nextAnswers, nextVariant)));
      setVariant(nextVariant);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      notify({ tone: 'error', message: err.message });
    } finally {
      setBusy(false);
    }
  };

  const addSkill = (skill) => {
    const next = { ...answers, skills: [...answers.skills, skill] };
    setAnswers(next);
    generate(variant, next);
  };

  if (result) {
    return (
      <WizardResult
        result={result}
        busy={busy}
        onReword={() => generate(variant + 1)}
        onAddSkill={addSkill}
        onBack={() => setResult(null)}
        onUse={() => onUse(result.resume, result.template)}
      />
    );
  }

  const steps = [
    <Step key="you" title="About you" hint="This goes at the top of your resume.">
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="Full name" value={answers.name} onChange={set('name')} placeholder="Asha Rao" />
        <TextField label="Email" type="email" value={answers.email} onChange={set('email')} placeholder="you@example.com" />
        <TextField label="Phone" type="tel" value={answers.phone} onChange={set('phone')} placeholder="+91 98765 43210" />
        <TextField label="City" value={answers.location} onChange={set('location')} placeholder="Hyderabad, India" />
        <TextField label="GitHub" value={answers.github} onChange={set('github')} placeholder="github.com/you" />
        <TextField label="LinkedIn" value={answers.linkedin} onChange={set('linkedin')} placeholder="linkedin.com/in/you" />
      </div>
    </Step>,
    <Step key="goal" title="Your goal" hint="We write the summary for this role. Paste a job post to tailor the whole resume to it.">
      <div className="space-y-4">
        <RoleField value={answers.target_role} onChange={set('target_role')} />
        <TextField
          label="Job description (optional)"
          multiline
          rows={6}
          value={answers.job_description}
          onChange={set('job_description')}
          placeholder="Paste the job post: matching skills and projects will be put first."
        />
      </div>
    </Step>,
    <Step key="edu" title="Education" hint="Your current or latest degree.">
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="Degree" value={answers.education.degree} onChange={setEdu('degree')} placeholder="B.Tech" />
        <TextField label="Branch / major" value={answers.education.branch} onChange={setEdu('branch')} placeholder="Computer Science (AI & ML)" />
        <div className="sm:col-span-2">
          <TextField label="College" value={answers.education.school} onChange={setEdu('school')} placeholder="Aditya University" />
        </div>
        <TextField label="Start year" value={answers.education.start} onChange={setEdu('start')} placeholder="2024" />
        <TextField label="Graduation year" value={answers.education.end} onChange={setEdu('end')} placeholder="2028" />
        <TextField label="CGPA or percentage" value={answers.education.grade} onChange={setEdu('grade')} placeholder="CGPA 8.6/10" />
      </div>
    </Step>,
    <Step
      key="items"
      title="Projects & internships"
      hint="Quick facts are enough: we turn them into strong bullet points. A number in the result makes the biggest difference."
    >
      <WizardItems items={answers.items} onChange={set('items')} />
    </Step>,
    <Step key="extras" title="Skills & extras" hint="Skills from your projects are added automatically. Add any others you have.">
      <div className="space-y-5">
        <TagInput label="Other skills" tags={answers.skills} onChange={set('skills')} placeholder="Statistics, Git, Figma…" />
        <div>
          <p className="label">Certifications</p>
          <LineList items={answers.certifications} onChange={set('certifications')} placeholder="[Google Data Analytics](https://coursera.org/verify/…)" addLabel="Add certification" />
        </div>
        <div>
          <p className="label">Achievements</p>
          <LineList items={answers.achievements} onChange={set('achievements')} placeholder="Top 5% in a national coding contest" addLabel="Add achievement" />
        </div>
      </div>
    </Step>,
  ];

  const last = step === steps.length - 1;
  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-bold tracking-[0.14em] text-muted uppercase">
            Step {step + 1} of {steps.length} · {STEPS[step]}
          </p>
          <div className="mt-2 flex gap-1.5" aria-hidden>
            {steps.map((_, i) => (
              <span key={i} className={`h-1.5 w-10 rounded-full ${i <= step ? 'bg-accent' : 'bg-line'}`} />
            ))}
          </div>
        </div>
        <Button variant="ghost" size="sm" icon={X} onClick={onCancel}>
          Cancel
        </Button>
      </div>

      {steps[step]}

      <div className="mt-5 flex items-center justify-between gap-3">
        <Button variant="secondary" icon={ArrowLeft} onClick={() => setStep((s) => s - 1)} disabled={step === 0}>
          Back
        </Button>
        {last ? (
          <Button variant="accent" icon={Sparkles} loading={busy} disabled={!ready} onClick={() => generate(0)}>
            Generate my resume
          </Button>
        ) : (
          <Button variant="primary" onClick={() => setStep((s) => s + 1)}>
            Next
            <ArrowRight className="size-4" aria-hidden />
          </Button>
        )}
      </div>
      {last && !ready && (
        <p className="mt-2 text-right text-xs text-muted">Add your name and at least one project or internship to generate.</p>
      )}
      <p className="mt-6 text-center text-xs text-muted">
        Written on our server from your answers by FitLens's own rules. Nothing is sent to an AI service.
      </p>
    </div>
  );
}
