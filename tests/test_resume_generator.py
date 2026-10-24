"""Automatic resume generation from quick answers (rule-based, no AI service)."""

from datetime import date
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.generator import GenerateEducation, GenerateItem, GenerateRequest
from app.services.ats_checker import ACTION_VERBS
from app.services.resume_generator import _level, generate_resume

client = TestClient(app)

JOB = (
    "Data Analyst (Entry level)\nRequirements:\n- SQL and Excel\n- Power BI or Tableau\n- Python (pandas)\n"
    "Nice to have:\n- Statistics, A/B testing"
)


def request(**overrides) -> GenerateRequest:
    data = dict(
        name="Asha Rao",
        email="asha@example.com",
        links=["github.com/asha-dev"],
        target_role="Data Analyst",
        education=[
            GenerateEducation(degree="B.Tech", branch="Computer Science", school="Aditya University", end="2028")
        ],
        items=[
            GenerateItem(
                title="Event Portal",
                tech=["React", "FastAPI"],
                what="worked on a registration portal for the college fest",
                impact="used by 1200 students",
            ),
            GenerateItem(
                title="Sales Dashboard",
                tech=["Power BI", "SQL", "Excel"],
                what="an interactive sales dashboard",
                details="data cleaning in SQL",
                impact="insights on 50000 orders",
                link="github.com/asha-dev/sales",
            ),
            GenerateItem(
                kind="internship",
                title="Data Analyst Intern",
                organization="Acme",
                date="May 2026 – Jul 2026",
                tech=["Python"],
                what="automated weekly KPI reports",
                impact="cut reporting time by 70%",
            ),
        ],
        skills=["Statistics"],
        job_description=JOB,
    )
    data.update(overrides)
    return GenerateRequest(**data)


def all_bullets(resume):
    return [b for entry in [*resume.experience, *resume.projects] for b in entry.bullets]


class BulletTests(unittest.TestCase):
    def test_bullets_start_with_action_verbs_and_end_cleanly(self):
        for bullet in all_bullets(generate_resume(request()).resume):
            with self.subTest(bullet=bullet):
                first = bullet.split()[0].lower()
                self.assertTrue(first in ACTION_VERBS, bullet)
                self.assertTrue(bullet.endswith("."))

    def test_weak_openers_removed_numbers_formatted_tech_named(self):
        bullets = all_bullets(generate_resume(request()).resume)
        portal = next(b for b in bullets if "registration portal" in b)
        self.assertNotIn("worked on", portal.lower())
        self.assertIn("1,200 students", portal)
        self.assertIn("React and FastAPI", portal)
        self.assertIn("Delivered insights on 50,000 orders.", bullets)
        self.assertIn("Cut reporting time by 70%.", bullets)

    def test_another_wording_keeps_the_facts(self):
        first = generate_resume(request(variant=0)).resume
        second = generate_resume(request(variant=1)).resume
        self.assertNotEqual(all_bullets(first), all_bullets(second))
        self.assertNotEqual(first.summary, second.summary)
        for text in ("1,200 students", "50,000 orders", "70%"):
            self.assertTrue(any(text in b for b in all_bullets(second)), text)


class TailoringTests(unittest.TestCase):
    def test_matching_project_first_and_skills_job_first(self):
        result = generate_resume(request())
        self.assertEqual(result.resume.projects[0].title, "Sales Dashboard")
        self.assertEqual(result.resume.projects[0].link, "github.com/asha-dev/sales")
        self.assertTrue(result.resume.summary.startswith("Third-year") or "Data Analyst" in result.resume.summary)
        skills_text = " ".join(result.resume.skills)
        self.assertLess(skills_text.index("SQL"), skills_text.index("React"))

    def test_never_adds_unlisted_skills_but_suggests_them(self):
        result = generate_resume(request())
        listed = " ".join(result.resume.skills).lower()
        self.assertNotIn("tableau", listed)
        self.assertNotIn("a/b testing", listed)
        self.assertIn("tableau", result.suggested_skills)
        self.assertIn("sql", result.matched_skills)

    def test_skills_are_grouped_rows(self):
        skills = generate_resume(request()).resume.skills
        self.assertTrue(any(s.startswith("Languages: ") for s in skills))
        self.assertTrue(any(s.startswith("Data & AI: ") for s in skills))


class LayoutTests(unittest.TestCase):
    def test_level_from_graduation_year(self):
        edu = lambda end: [GenerateEducation(end=end)]  # noqa: E731
        today = date(2026, 10, 24)
        self.assertEqual(_level(edu("2027"), today), ("Final-year", False))
        self.assertEqual(_level(edu("2028"), today), ("Third-year", False))
        self.assertEqual(_level(edu("2026"), today), ("Recent", True))
        self.assertEqual(_level([], today), ("", False))

    def test_extra_projects_left_out_with_a_note(self):
        items = [GenerateItem(title=f"Project {i}", what="a small web app", impact=f"{i}0 users") for i in range(6)]
        result = generate_resume(request(items=items, job_description=""))
        self.assertEqual(len(result.resume.projects), 4)
        self.assertTrue(any("Left out" in note for note in result.notes))

    def test_missing_numbers_and_links_get_tips(self):
        items = [GenerateItem(title="Notes App", what="a notes app")]
        result = generate_resume(request(items=items, links=[], job_description=""))
        self.assertTrue(any("Add a number" in note for note in result.notes))
        self.assertTrue(any("GitHub" in note for note in result.notes))

    def test_empty_request_still_works(self):
        result = generate_resume(GenerateRequest())
        self.assertEqual(result.resume.projects, [])
        self.assertIn(result.template, ("tech-classic", "tech-compact"))


class EndpointTests(unittest.TestCase):
    def test_generate_endpoint(self):
        response = client.post("/api/resume/generate", json=request().model_dump())
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["resume"]["name"], "Asha Rao")
        self.assertIn(body["template"], ("tech-classic", "tech-compact"))

    def test_rejects_bad_input(self):
        self.assertEqual(client.post("/api/resume/generate", json={"variant": -1}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
