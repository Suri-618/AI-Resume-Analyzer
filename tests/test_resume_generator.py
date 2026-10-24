"""Automatic resume generation from quick answers (rule-based, no AI service)."""

from datetime import date
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.generator import (
    GenerateActivity,
    GenerateEducation,
    GenerateItem,
    GenerateRequest,
    ProjectIdeasRequest,
)
from app.services.ats_checker import ACTION_VERBS
from app.services.resume_generator import _level, generate_resume, suggest_projects

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

    def test_project_ideas_endpoint(self):
        response = client.post("/api/resume/project-ideas", json={"target_role": "Data Analyst", "skills": []})
        self.assertEqual(response.status_code, 200, response.text)
        projects = response.json()["projects"]
        self.assertTrue(1 <= len(projects) <= 3)
        self.assertTrue(all(p["bullet"] and p["steps"] for p in projects))


class FresherTests(unittest.TestCase):
    """Students with few or no projects: activities and project ideas."""

    ACTIVITIES = [
        GenerateActivity(
            role="Event Coordinator",
            organization="Coding Club",
            date="2025",
            what="organised a hackathon for 300 students",
        ),
        GenerateActivity(role="Volunteer", organization="NSS", what="blood donation drive with 150 donors"),
        GenerateActivity(role="Member", organization="Robotics Club", what="helped build a line-follower robot"),
        GenerateActivity(
            role="Participant", organization="Smart India Hackathon", what="participated in the national finals"
        ),
        GenerateActivity(role="Volunteer", organization="Rotaract", what="helped in organizing an awareness event"),
    ]

    def test_activities_section_is_honest_and_polished(self):
        result = generate_resume(GenerateRequest(name="Ravi", activities=self.ACTIVITIES))
        section = result.resume.additional[0]
        self.assertEqual(section.heading, "Leadership & Activities")
        self.assertEqual(
            section.items,
            [
                "Event Coordinator, Coding Club (2025): Organised a hackathon for 300 students.",
                "Volunteer, NSS: Contributed to a blood donation drive with 150 donors.",
                "Member, Robotics Club: Collaborated to build a line-follower robot.",
                "Participant, Smart India Hackathon: Participated in the national finals.",
                "Volunteer, Rotaract: Contributed to organizing an awareness event.",
            ],
        )

    def test_first_year_with_no_projects_still_gets_a_resume_and_a_tip(self):
        result = generate_resume(
            GenerateRequest(
                name="Ravi",
                target_role="Software Engineer",
                education=[GenerateEducation(degree="B.Tech", branch="Computer Science", end="2030")],
                skills=["Python", "C"],
            )
        )
        self.assertTrue(result.resume.summary.startswith("First-year"))
        self.assertTrue(any("No projects yet" in note for note in result.notes))
        self.assertIn("python", result.matched_skills)

    def test_helped_is_never_upgraded_to_built(self):
        items = [GenerateItem(title="Arm", what="helped build a robot arm", tech=["Arduino"])]
        bullet = generate_resume(GenerateRequest(name="R", items=items)).resume.projects[0].bullets[0]
        self.assertTrue(bullet.startswith("Collaborated to build a robot arm"), bullet)

    def test_project_ideas_teach_missing_skills(self):
        ideas = suggest_projects(ProjectIdeasRequest(target_role="Data Analyst", skills=["Excel"])).projects
        self.assertTrue(ideas)
        self.assertTrue(all("excel" not in p.closes for p in ideas))


if __name__ == "__main__":
    unittest.main()
