"""Generate a complete, ATS-friendly resume from a student's quick answers.

No AI service is involved: the text is assembled from the student's own facts
with writing rules (strong action verbs, the technology used, a measurable
result, numbers formatted) and the project's curated data (target roles and
their skills, the job decoder). The student only ever gets skills they listed;
skills the job or role asks for that they did not list come back as
suggestions to confirm. ``variant`` rotates verbs and sentence patterns, so
"Try another wording" gives a different but equally factual draft.

The function signature is the seam for an optional AI writer later: it could
take the same GenerateRequest and return the same GenerateResponse.
"""

from __future__ import annotations

from datetime import date
import re

from app.schemas.generator import GenerateEducation, GenerateItem, GenerateRequest, GenerateResponse
from app.schemas.resume import ResumeEntry, StructuredResume
from app.services.ats_checker import ACTION_VERBS
from app.services.job_decoder import decode_job
from app.services.role_gap import target_roles
from app.services.skill_extractor import extract_skills

MAX_PROJECTS = 4
MAX_BULLETS = 3
# Estimated lines that fit on one A4 page in Tech Classic; beyond this, use Tech Compact
ONE_PAGE_LINES = 54

# Skill rows, in display order. Matched on the canonical skill or the typed name.
SKILL_GROUPS: list[tuple[str, frozenset[str]]] = [
    (
        "Languages",
        frozenset(
            "python java c++ c# c javascript typescript sql php r ruby scala kotlin swift go rust "
            "matlab bash dart html css".split()
        ),
    ),
    (
        "Frameworks & Web",
        frozenset(
            [
                *"react angular vue node.js django flask spring fastapi express next.js tailwind "
                "bootstrap flutter streamlit graphql".split(),
                "rest api",
                "tailwind css",
                "react native",
                ".net",
            ]
        ),
    ),
    (
        "Data & AI",
        frozenset(
            [
                *"pandas numpy scikit-learn tensorflow pytorch keras opencv statistics spark hadoop "
                "nlp llms langchain matplotlib seaborn".split(),
                "machine learning",
                "deep learning",
                "data science",
                "natural language processing",
                "computer vision",
                "data analysis",
                "data visualization",
                "power bi",
                "tableau",
                "excel",
                "generative ai",
                "hugging face",
            ]
        ),
    ),
    (
        "Databases",
        frozenset("mysql postgresql mongodb sqlite oracle redis firebase supabase dynamodb".split()),
    ),
    (
        "Cloud & DevOps",
        frozenset(
            [
                *"aws azure gcp docker kubernetes linux terraform jenkins vercel render netlify".split(),
                "ci/cd",
                "github actions",
            ]
        ),
    ),
    ("Tools", frozenset("git github gitlab jira figma postman vs code agile scrum".split() + ["vs code"])),
]

_ML = re.compile(r"\b(model|predict|classif|regress|train|neural|machine learning|ml|nlp|llm|ai|detect)", re.I)
_DATA = re.compile(r"\b(analy|insight|eda|data set|dataset|survey|trend)", re.I)
_API = re.compile(r"\b(api|backend|server|service|microservice|database|pipeline)", re.I)
_AUTO = re.compile(r"\b(automat|script|bot|scraper|workflow|cron)", re.I)
_APP = re.compile(r"\b(app|website|web site|portal|platform|dashboard|extension|tool|system|clone)", re.I)
_PEOPLE = re.compile(r"\b(users?|students?|employees|people|customers|members|visitors|clients|downloads)\b", re.I)
_SCORE = re.compile(r"\b(accuracy|precision|recall|f1|score|rank|rating|auc|r2|r²)\b", re.I)
_USED_BY = re.compile(r"^(used|adopted|loved|downloaded|trusted)\s+by\b", re.I)
_WEAK_START = re.compile(
    r"^(i\s+|we\s+)?(worked on|working on|helped( to)?|assisted( in)?|involved in|responsible for|"
    r"participated in|did|made|was|were|created a project (on|for))\s+",
    re.I,
)

LEAD_VERBS = {
    "ml": ["Trained", "Developed", "Built"],
    "data": ["Analyzed", "Built", "Created"],
    "auto": ["Automated", "Built", "Developed"],
    "api": ["Developed", "Built", "Designed"],
    "app": ["Built", "Developed", "Designed"],
    "other": ["Built", "Developed", "Created"],
}
# Only verbs the bullet coach (ACTION_VERBS) accepts, so generated bullets rate as strong
# "Implemented" reads well with things and processes ("data cleaning"); "Developed" only with things
DETAIL_VERBS = ["Implemented", "Developed"]
_PROCESS = re.compile(r"^\W*(?:\w+\s+){0,2}?\w+(?:ing|tion|sion|sis|ment)\b", re.I)


# ---------------------------------------------------------------------------- text helpers
def _sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip()).rstrip(" .;,")
    return f"{text[:1].upper()}{text[1:]}." if text else ""


def _lower_first(text: str) -> str:
    """Lower-case the first letter unless it starts an acronym or name (API, React)."""
    text = (text or "").strip()
    if len(text) > 1 and text[1].isupper():
        return text
    return text[:1].lower() + text[1:]


def _format_numbers(text: str) -> str:
    """1200 -> 1,200 (years and decimals are left alone)."""

    def fix(match: re.Match) -> str:
        value = match.group(0)
        if re.fullmatch(r"(19|20)\d{2}", value):
            return value
        return f"{int(value):,}"

    return re.sub(r"(?<![\d.,])\d{4,9}(?![\d.,])", fix, text or "")


def _join(items: list[str]) -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def _strip_weak_start(text: str) -> str:
    return _WEAK_START.sub("", (text or "").strip())


def _starts_with_verb(text: str) -> bool:
    first = re.sub(r"[^a-z]", "", (text or "").split(" ")[0].lower()) if text.strip() else ""
    return first in ACTION_VERBS or first in {"cut", "won", "led", "grew", "saved", "served", "reached", "sped"}


def _canonical(term: str) -> str | None:
    found = extract_skills((term or "").lower())
    return next(iter(found)) if len(found) == 1 else None


def _kind_of(text: str) -> str:
    # Build words win over data words: "a sales dashboard" was built, not analysed
    for kind, pattern in (("ml", _ML), ("auto", _AUTO), ("api", _API), ("app", _APP), ("data", _DATA)):
        if pattern.search(text):
            return kind
    return "other"


# ---------------------------------------------------------------------------- tailoring
class _Target:
    """What the job (if pasted) and the target role ask for."""

    def __init__(self, request: GenerateRequest, claimed: set[str]):
        self.role_skills = target_roles().get(request.target_role, [])
        self.must: list[str] = []
        self.nice: list[str] = []
        if request.job_description.strip():
            insights = decode_job(request.job_description, claimed)
            self.must = insights.must_have
            self.nice = insights.nice_to_have + insights.also_mentioned
        self.wanted = list(dict.fromkeys([*self.must, *self.nice, *self.role_skills]))

    def weight(self, canonical: str | None) -> int:
        if not canonical:
            return 0
        if canonical in self.must:
            return 3
        if canonical in self.nice:
            return 2
        return 1 if canonical in self.role_skills else 0


# ---------------------------------------------------------------------------- sections
def _bullets(item: GenerateItem, tech: list[str], variant: int) -> list[str]:
    what = _strip_weak_start(item.what)
    details = _strip_weak_start(item.details)
    impact = _format_numbers(item.impact.strip().rstrip("."))
    kind = _kind_of(f"{item.what} {item.details} {item.title}")
    bullets: list[str] = []

    if what:
        if _starts_with_verb(what):
            lead = what
        else:
            verbs = LEAD_VERBS[kind]
            lead = f"{verbs[variant % len(verbs)]} {_lower_first(what)}"
        named = [t for t in tech[:3] if t.lower() not in lead.lower()]
        if named:
            lead += f" {'using' if variant % 2 == 0 else 'with'} {_join(named)}"
        if impact and _USED_BY.match(impact):
            lead += f", {_lower_first(impact)}"
            impact = ""
        bullets.append(_sentence(_format_numbers(lead)))

    if details:
        if _starts_with_verb(details):
            bullets.append(_sentence(_format_numbers(details)))
        else:
            # Alternate with the wording variant, but never repeat the verb that opens the first bullet
            used = bullets[0].split(" ")[0] if bullets else ""
            options = ["Implemented"] if _PROCESS.match(details) else DETAIL_VERBS
            options = [v for v in options if v != used] or ["Implemented"]
            verb = options[variant % len(options)]
            bullets.append(_sentence(f"{verb} {_lower_first(_format_numbers(details))}"))

    if impact:
        if _starts_with_verb(impact):
            bullets.append(_sentence(impact))
        elif _USED_BY.match(impact):
            bullets.append(_sentence(f"Delivered a solution {_lower_first(impact)}"))
        else:
            if _SCORE.search(impact):
                verb = "Achieved"
            elif _PEOPLE.search(impact) and re.match(r"^[\d,.+]+\s", impact):
                verb = "Supported"
            else:
                verb = "Delivered"
            bullets.append(_sentence(f"{verb} {_lower_first(impact)}"))
    return bullets[:MAX_BULLETS]


def _tech_order(item: GenerateItem, target: _Target) -> list[str]:
    tech = [t.strip() for t in item.tech if t.strip()]
    return sorted(tech, key=lambda t: -target.weight(_canonical(t)))


def _entry(item: GenerateItem, target: _Target, variant: int) -> ResumeEntry:
    tech = _tech_order(item, target)
    if item.kind == "project":
        title = item.title.strip() or "Project"
        subtitle = ", ".join(tech)
    else:
        title = ", ".join(x for x in (item.title.strip(), item.organization.strip()) if x) or "Internship"
        subtitle = ""
    return ResumeEntry(
        title=title,
        subtitle=subtitle,
        date=item.date.strip(),
        link=item.link.strip(),
        bullets=_bullets(item, tech, variant),
    )


def _score(item: GenerateItem, target: _Target) -> int:
    return sum(target.weight(_canonical(t)) for t in item.tech) + (1 if item.impact.strip() else 0)


def _skills(request: GenerateRequest, target: _Target) -> tuple[list[str], set[str]]:
    """Skill rows as 'Label: first', 'second', ... items, and the canonical skills claimed."""
    typed: list[str] = []
    for raw in [*(t for item in request.items for t in item.tech), *request.skills]:
        name = raw.strip()
        if name and name.lower() not in {t.lower() for t in typed}:
            typed.append(name)
    claimed = {c for c in (_canonical(t) for t in typed) if c}

    rows: dict[str, list[str]] = {}
    for name in typed:
        canonical = _canonical(name)
        keys = {name.lower(), canonical or ""}
        label = next((g for g, members in SKILL_GROUPS if keys & members), "Other")
        rows.setdefault(label, []).append(name)

    out: list[str] = []
    for label in [g for g, _ in SKILL_GROUPS] + ["Other"]:
        if label not in rows:
            continue
        ordered = sorted(rows[label], key=lambda n: -target.weight(_canonical(n)))
        out.append(f"{label}: {ordered[0]}")
        out.extend(ordered[1:])
    return out, claimed


def _top_skills(request: GenerateRequest, target: _Target) -> list[str]:
    """The student's skills, most wanted by the job or role first."""
    typed = list(dict.fromkeys(t.strip() for item in request.items for t in item.tech if t.strip()))
    typed += [s.strip() for s in request.skills if s.strip() and s.strip() not in typed]
    return sorted(typed, key=lambda t: -target.weight(_canonical(t)))


def _level(education: list[GenerateEducation], today: date) -> tuple[str, bool]:
    """('Final-year', False) ... or ('Recent', True) when already graduated."""
    years = [int(m) for e in education for m in re.findall(r"(?:19|20)\d{2}", e.end)]
    if not years:
        return "", False
    end = max(years)
    # Academic years end around June
    left = end - today.year - (0 if today.month < 7 else 1)
    if left < 0:
        return "Recent", True
    return {0: "Final-year", 1: "Third-year", 2: "Second-year"}.get(left, "First-year"), False


def _summary(request: GenerateRequest, top_skills: list[str], entries_count: tuple[int, int], variant: int) -> str:
    edu = request.education[0] if request.education else GenerateEducation()
    level, graduated = _level(request.education, date.today())
    degree = " ".join(x for x in (edu.degree.strip(), edu.branch.strip()) if x)
    person = f"{level} {degree} {'graduate' if graduated else 'student'}".strip()
    person = re.sub(r"\s+", " ", person) if degree or level else ("Graduate" if graduated else "Student")
    role = request.target_role.strip()
    top = _join(top_skills[:4])
    projects, roles = entries_count
    experience = []
    if projects:
        experience.append(f"{projects} project{'s' if projects > 1 else ''}")
    if roles:
        experience.append(f"{roles} internship{'s' if roles > 1 else ''}")
    built = _join(experience)

    a = person[:1].upper() + person[1:]
    if variant % 2 == 0:
        parts = [f"{a}{f' aiming for {role} roles' if role else ''}."]
        if top:
            parts.append(f"Skilled in {top}{f', with hands-on experience from {built}' if built else ''}.")
    else:
        # "Aspiring Data Analyst and third-year B.Tech ... student"
        lowered = person[:1].lower() + person[1:] if level else person
        lead = f"Aspiring {role} and {lowered}" if role else a
        parts = [f"{lead} who learns by building{f' ({built})' if built else ''}."]
        if top:
            parts.append(f"Comfortable with {top}, and quick to pick up new tools.")
    return " ".join(parts)


def _headline(request: GenerateRequest) -> str:
    edu = request.education[0] if request.education else GenerateEducation()
    _, graduated = _level(request.education, date.today())
    field = edu.branch.strip()
    role = request.target_role.strip()
    if not field and not role:
        return ""
    who = f"{field} {'Graduate' if graduated else 'Student'}" if field else ("Graduate" if graduated else "Student")
    return f"{who} | Aspiring {role}" if role else who


def _estimated_lines(resume: StructuredResume) -> int:
    lines = 5 + 2 * 7  # header + headings
    lines += max(1, len(resume.summary) // 95 + 1)
    lines += sum(1 for s in resume.skills if ":" in s) or 1
    for entry in [*resume.experience, *resume.projects, *resume.education]:
        lines += 1 + (1 if entry.subtitle else 0) + sum(len(b) // 95 + 1 for b in entry.bullets)
    lines += len(resume.certifications) + len(resume.achievements)
    return lines


# ---------------------------------------------------------------------------- entry point
def generate_resume(request: GenerateRequest) -> GenerateResponse:
    skills, claimed = _skills(request, _Target(request, set()))
    target = _Target(request, claimed)
    skills, claimed = _skills(request, target)
    notes: list[str] = []

    items = [i for i in request.items if i.title.strip() or i.what.strip()]
    projects = sorted((i for i in items if i.kind == "project"), key=lambda i: -_score(i, target))
    roles = [i for i in items if i.kind != "project"]
    if len(projects) > MAX_PROJECTS:
        dropped = ", ".join(p.title for p in projects[MAX_PROJECTS:])
        notes.append(f"Left out {dropped} to keep one page; the projects that match best come first.")
        projects = projects[:MAX_PROJECTS]
    for item in items:
        if not item.impact.strip() or not re.search(r"\d", item.impact):
            label = item.title or item.what
            notes.append(f"Add a number to “{label}” (users, accuracy, time saved): recruiters look for impact.")

    education = [
        ResumeEntry(
            title=" in ".join(x for x in (e.degree.strip(), e.branch.strip()) if x),
            subtitle=" · ".join(x for x in (e.school.strip(), e.grade.strip()) if x),
            date=" – ".join(x for x in (e.start.strip(), e.end.strip()) if x),
        )
        for e in request.education
        if e.degree.strip() or e.branch.strip() or e.school.strip()
    ]

    resume = StructuredResume(
        name=request.name.strip(),
        headline=_headline(request),
        email=request.email.strip(),
        phone=request.phone.strip(),
        location=request.location.strip(),
        links=[x.strip() for x in request.links if x.strip()],
        summary=_summary(request, _top_skills(request, target), (len(projects), len(roles)), request.variant),
        skills=skills,
        experience=[_entry(i, target, request.variant) for i in roles],
        projects=[_entry(i, target, request.variant) for i in projects],
        education=education,
        certifications=[c.strip() for c in request.certifications if c.strip()],
        achievements=[a.strip() for a in request.achievements if a.strip()],
    )

    template = "tech-classic"
    if _estimated_lines(resume) > ONE_PAGE_LINES:
        template = "tech-compact"
        notes.append("It's a full resume, so it uses the Tech Compact template to stay on one page.")

    matched = [s for s in target.wanted if s in claimed]
    suggested = [s for s in target.wanted if s not in claimed][:10]
    if not request.links:
        notes.append("Add your GitHub and LinkedIn links: recruiters check them.")
    return GenerateResponse(
        resume=resume, template=template, matched_skills=matched, suggested_skills=suggested, notes=notes[:6]
    )
