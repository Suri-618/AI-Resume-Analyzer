import { ArrowUpRight, ChevronDown, Hammer, Lightbulb, Plus } from 'lucide-react';
import { useState } from 'react';
import { fetchProjectIdeas } from '../../lib/api';
import { formatSkill } from '../../utils/format';
import Button from '../ui/Button';

function IdeaCard({ idea, onAdd }) {
  const [open, setOpen] = useState(false);
  const skills = [...idea.closes, ...idea.uses, ...idea.also_learn];
  return (
    <li className="rounded-2xl border border-line bg-card p-4">
      <div className="flex items-start gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-highlight/70 text-ink">
          <Hammer className="size-4" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-semibold">{idea.title}</p>
          <p className="text-xs text-muted">
            {idea.level} · about {idea.hours} hours
          </p>
          <p className="mt-1.5 text-sm">{idea.summary}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {idea.closes.map((s) => (
              <span key={s} className="rounded-md bg-highlight/60 px-1.5 py-0.5 text-xs font-medium">
                {formatSkill(s)}
              </span>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setOpen((x) => !x)}
            className="mt-2 inline-flex cursor-pointer items-center gap-1 text-sm font-semibold text-accent"
            aria-expanded={open}
          >
            How to build it
            <ChevronDown className={`size-4 transition ${open ? 'rotate-180' : ''}`} aria-hidden />
          </button>
          {open && (
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-muted">
              {idea.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          )}
          <p className="mt-3 rounded-xl border border-dashed border-line px-3 py-2 text-xs">
            <span className="font-semibold">Resume bullet when it's done: </span>
            <span className="italic">{idea.bullet}</span>
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <a
              href={`/learn?skills=${encodeURIComponent(idea.closes.join(','))}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-line px-3 text-xs font-semibold hover:border-ink/40"
            >
              Learn these skills
              <ArrowUpRight className="size-3.5" aria-hidden />
            </a>
            <Button variant="ghost" size="sm" icon={Plus} onClick={() => onAdd(idea, skills)}>
              I've built this, add it
            </Button>
          </div>
        </div>
      </div>
    </li>
  );
}

/** "No projects yet?": portfolio projects for the target role, with steps and the bullet they earn. */
export default function ProjectIdeas({ role, skills, jobDescription, onAdd, notify }) {
  const [state, setState] = useState({ loading: false, ideas: null });

  const load = async () => {
    setState({ loading: true, ideas: null });
    try {
      const data = await fetchProjectIdeas({ targetRole: role, skills, jobDescription });
      setState({ loading: false, ideas: data.projects });
    } catch (err) {
      setState({ loading: false, ideas: null });
      notify({ tone: 'error', message: err.message });
    }
  };

  return (
    <div className="mt-5 rounded-2xl border border-dashed border-accent/40 bg-accent-soft/30 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="flex items-center gap-2 text-sm">
          <Lightbulb className="size-4 text-accent" aria-hidden />
          <span>
            <span className="font-semibold">No projects yet, or only one?</span> See projects that teach what{' '}
            {role ? `a ${role}` : 'your target role'} needs.
          </span>
        </p>
        <Button variant="secondary" size="sm" loading={state.loading} onClick={load}>
          {state.ideas ? 'Refresh ideas' : 'Show project ideas'}
        </Button>
      </div>
      {state.ideas && state.ideas.length === 0 && (
        <p className="mt-3 text-sm text-muted">Pick a target role in step 2 to get matching ideas.</p>
      )}
      {state.ideas?.length > 0 && (
        <>
          <ul className="mt-4 space-y-3">
            {state.ideas.map((idea) => (
              <IdeaCard key={idea.id} idea={idea} onAdd={onAdd} />
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted">Only add a project once you've built it: interviewers will ask about it.</p>
        </>
      )}
    </div>
  );
}
