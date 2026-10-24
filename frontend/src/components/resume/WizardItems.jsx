import { AnimatePresence, motion } from 'framer-motion';
import { Plus, Trash2 } from 'lucide-react';
import { emptyWizardItem as emptyItem } from '../../lib/resume';
import { TagInput, TextField } from '../results/edit/fields';
import Button from '../ui/Button';

const KINDS = [
  { id: 'project', label: 'Project' },
  { id: 'internship', label: 'Internship' },
  { id: 'job', label: 'Job' },
];

function ItemCard({ item, index, onChange, onRemove }) {
  const set = (key) => (value) => onChange({ ...item, [key]: value });
  const project = item.kind === 'project';
  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: 40 }}
      className="rounded-2xl border border-line bg-sunken/40 p-4"
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div role="radiogroup" aria-label={`Type of entry ${index + 1}`} className="inline-flex rounded-xl bg-card p-1">
          {KINDS.map((k) => (
            <button
              key={k.id}
              type="button"
              role="radio"
              aria-checked={item.kind === k.id}
              onClick={() => set('kind')(k.id)}
              className={`cursor-pointer rounded-lg px-3 py-1 text-sm font-semibold ${
                item.kind === k.id ? 'bg-highlight text-ink' : 'text-muted hover:text-ink'
              }`}
            >
              {k.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="cursor-pointer rounded-lg p-1.5 text-muted hover:bg-pen-soft hover:text-pen"
          aria-label={`Remove ${item.title || 'entry'}`}
        >
          <Trash2 className="size-4" />
        </button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <TextField
          label={project ? 'Project name' : 'Your role'}
          value={item.title}
          onChange={set('title')}
          placeholder={project ? 'Event Registration Portal' : 'Data Analyst Intern'}
        />
        {project ? (
          <TextField label="When (optional)" value={item.date} onChange={set('date')} placeholder="2025" />
        ) : (
          <TextField label="Company" value={item.organization} onChange={set('organization')} placeholder="Acme Analytics" />
        )}
        {!project && <TextField label="Dates" value={item.date} onChange={set('date')} placeholder="May 2026 – Jul 2026" />}
        <div className={project ? 'sm:col-span-2' : ''}>
          <TagInput label="Tech used" tags={item.tech} onChange={set('tech')} placeholder="React, FastAPI, PostgreSQL…" />
        </div>
        <div className="sm:col-span-2">
          <TextField
            label="What did you build or do?"
            value={item.what}
            onChange={set('what')}
            placeholder={project ? 'a registration portal for the college fest' : 'automated weekly KPI reports'}
          />
        </div>
        <div className="sm:col-span-2">
          <TextField
            label="Key technical work (optional)"
            value={item.details}
            onChange={set('details')}
            placeholder="JWT login, email reminders and a waitlist"
          />
        </div>
        <div className="sm:col-span-2">
          <TextField
            label="Result, with a number (optional but powerful)"
            value={item.impact}
            onChange={set('impact')}
            placeholder="used by 1,200 students · 96% accuracy · cut reporting time by 70%"
          />
        </div>
        <div className="sm:col-span-2">
          <TextField label="Link (optional)" type="url" value={item.link} onChange={set('link')} placeholder="github.com/you/project" />
        </div>
      </div>
    </motion.li>
  );
}

/** Projects, internships and jobs as quick facts. */
export default function WizardItems({ items, onChange }) {
  const update = (id, next) => onChange(items.map((x) => (x._id === id ? next : x)));
  return (
    <div>
      <ul className="space-y-3">
        <AnimatePresence initial={false}>
          {items.map((item, i) => (
            <ItemCard
              key={item._id}
              item={item}
              index={i}
              onChange={(next) => update(item._id, next)}
              onRemove={() => onChange(items.filter((x) => x._id !== item._id))}
            />
          ))}
        </AnimatePresence>
      </ul>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button variant="secondary" size="sm" icon={Plus} onClick={() => onChange([...items, emptyItem('project')])}>
          Add project
        </Button>
        <Button variant="ghost" size="sm" icon={Plus} onClick={() => onChange([...items, emptyItem('internship')])}>
          Add internship
        </Button>
      </div>
    </div>
  );
}
