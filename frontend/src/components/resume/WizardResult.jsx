import { motion } from 'framer-motion';
import { ArrowLeft, Check, Lightbulb, Plus, RefreshCw } from 'lucide-react';
import { templateById } from '../../lib/templates';
import { formatSkill } from '../../utils/format';
import Button from '../ui/Button';
import ScaledPage from './ScaledPage';

/** The generated resume with tips, suggested skills and the next actions. */
export default function WizardResult({ result, busy, onReword, onAddSkill, onBack, onUse }) {
  const template = templateById(result.template);
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="card p-3 sm:p-4">
        <p className="mb-3 px-1 text-sm font-semibold">{template.name} template</p>
        <div className="overflow-hidden rounded-lg shadow-[0_1px_6px_rgba(0,0,0,0.15)]">
          <ScaledPage resume={result.resume} templateId={result.template} />
        </div>
      </div>

      <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
        <div className="card p-4">
          <h3 className="font-display text-lg font-semibold">Your resume is ready</h3>
          <p className="mt-1 text-sm text-muted">Written from your answers. Open it in the builder to edit anything.</p>
          <div className="mt-4 flex flex-col gap-2">
            <Button variant="accent" icon={Check} onClick={onUse}>
              Use this resume
            </Button>
            <Button variant="secondary" icon={RefreshCw} loading={busy} onClick={onReword}>
              Try another wording
            </Button>
            <Button variant="ghost" icon={ArrowLeft} onClick={onBack}>
              Change my answers
            </Button>
          </div>
        </div>

        {result.suggested_skills.length > 0 && (
          <div className="card p-4">
            <h3 className="font-semibold">Skills this job or role asks for</h3>
            <p className="mt-1 text-xs text-muted">Not on your resume yet. Add only the ones you really have.</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {result.suggested_skills.map((skill) => (
                <button
                  key={skill}
                  type="button"
                  disabled={busy}
                  onClick={() => onAddSkill(formatSkill(skill))}
                  className="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-dashed border-pen/50 px-2 py-1 text-xs font-semibold text-pen hover:bg-pen-soft disabled:opacity-50"
                >
                  <Plus className="size-3" aria-hidden />
                  {formatSkill(skill)}
                </button>
              ))}
            </div>
          </div>
        )}

        {result.matched_skills.length > 0 && (
          <div className="card p-4">
            <h3 className="font-semibold">Matches the job or role</h3>
            <p className="mt-2 text-sm">{result.matched_skills.map(formatSkill).join(', ')}</p>
          </div>
        )}

        {result.notes.length > 0 && (
          <div className="card p-4">
            <h3 className="flex items-center gap-1.5 font-semibold">
              <Lightbulb className="size-4 text-accent" aria-hidden />
              Make it stronger
            </h3>
            <ul className="mt-2 space-y-1.5 text-sm text-muted">
              {result.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </div>
        )}
      </aside>
    </motion.div>
  );
}
