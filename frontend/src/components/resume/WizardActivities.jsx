import { AnimatePresence, motion } from 'framer-motion';
import { Plus, Trash2 } from 'lucide-react';
import { emptyWizardActivity } from '../../lib/resume';
import { TextField } from '../results/edit/fields';
import Button from '../ui/Button';

const EXAMPLES = ['Coding club', 'Tech fest', 'Hackathon', 'NSS / NCC', 'Sports team', 'Volunteering', 'Class representative'];

/** Clubs, events, hackathons, NSS/NCC and volunteering: often most of what a fresher has. */
export default function WizardActivities({ activities, onChange }) {
  const update = (id, key, value) => onChange(activities.map((a) => (a._id === id ? { ...a, [key]: value } : a)));
  return (
    <div>
      <p className="mb-3 text-xs text-muted">Ideas: {EXAMPLES.join(' · ')}</p>
      <ul className="space-y-3">
        <AnimatePresence initial={false}>
          {activities.map((activity, i) => (
            <motion.li
              key={activity._id}
              layout
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: 40 }}
              className="rounded-2xl border border-line bg-sunken/40 p-4"
            >
              <div className="mb-2 flex items-center justify-between">
                <span className="font-mono text-xs text-muted">#{i + 1}</span>
                <button
                  type="button"
                  onClick={() => onChange(activities.filter((a) => a._id !== activity._id))}
                  className="cursor-pointer rounded-lg p-1.5 text-muted hover:bg-pen-soft hover:text-pen"
                  aria-label={`Remove ${activity.role || 'activity'}`}
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <TextField label="Your role" value={activity.role} onChange={(v) => update(activity._id, 'role', v)} placeholder="Event Coordinator · Volunteer · Member" />
                <TextField label="Club, event or group" value={activity.organization} onChange={(v) => update(activity._id, 'organization', v)} placeholder="Coding Club · NSS · Tech fest" />
                <div className="sm:col-span-2">
                  <TextField
                    label="What did you do? (a number helps)"
                    value={activity.what}
                    onChange={(v) => update(activity._id, 'what', v)}
                    placeholder="organised a 24-hour hackathon for 300 students"
                  />
                </div>
                <TextField label="When (optional)" value={activity.date} onChange={(v) => update(activity._id, 'date', v)} placeholder="2025" />
              </div>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
      <Button variant="secondary" size="sm" icon={Plus} className="mt-3" onClick={() => onChange([...activities, emptyWizardActivity()])}>
        Add activity
      </Button>
    </div>
  );
}
