"""Schemas for automatic resume generation from a student's quick answers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.insights import ProjectPick
from app.schemas.resume import StructuredResume

SHORT = 300
LIST = 40


class GenerateEducation(BaseModel):
    degree: str = Field("", max_length=80, description="e.g. 'B.Tech'")
    branch: str = Field("", max_length=120, description="e.g. 'Computer Science (AI & ML)'")
    school: str = Field("", max_length=150)
    start: str = Field("", max_length=20)
    end: str = Field("", max_length=20, description="Graduation year, e.g. '2027'")
    grade: str = Field("", max_length=40, description="e.g. 'CGPA 8.6/10' or '86%'")


class GenerateItem(BaseModel):
    """One project, internship or job, described in quick facts."""

    kind: Literal["project", "internship", "job"] = "project"
    title: str = Field("", max_length=150, description="Project name, or the role for internships and jobs")
    organization: str = Field("", max_length=150, description="Company or organisation (internships and jobs)")
    date: str = Field("", max_length=60)
    tech: list[str] = Field(default_factory=list, max_length=LIST)
    what: str = Field("", max_length=SHORT, description="What you built or did, in a few words")
    details: str = Field("", max_length=SHORT, description="Key technical work (optional)")
    impact: str = Field("", max_length=SHORT, description="The result, ideally with a number (optional)")
    link: str = Field("", max_length=300)


class GenerateActivity(BaseModel):
    """A club, event, hackathon, NSS/NCC, volunteering or other activity."""

    role: str = Field("", max_length=120, description="e.g. 'Event Coordinator' or 'Volunteer'")
    organization: str = Field("", max_length=150, description="e.g. 'Coding Club' or 'NSS'")
    date: str = Field("", max_length=60)
    what: str = Field("", max_length=SHORT, description="What you did, ideally with a number")


class GenerateRequest(BaseModel):
    name: str = Field("", max_length=120)
    email: str = Field("", max_length=200)
    phone: str = Field("", max_length=60)
    location: str = Field("", max_length=120)
    links: list[str] = Field(default_factory=list, max_length=10)
    target_role: str = Field("", max_length=80)
    education: list[GenerateEducation] = Field(default_factory=list, max_length=6)
    items: list[GenerateItem] = Field(default_factory=list, max_length=12)
    skills: list[str] = Field(default_factory=list, max_length=80, description="Extra skills beyond the projects' tech")
    certifications: list[str] = Field(default_factory=list, max_length=20)
    achievements: list[str] = Field(default_factory=list, max_length=20)
    activities: list[GenerateActivity] = Field(default_factory=list, max_length=12)
    job_description: str = Field("", max_length=20_000, description="Optional; tailors the resume to this job")
    variant: int = Field(0, ge=0, le=1000, description="Changes the wording ('Try another wording')")


class GenerateResponse(BaseModel):
    resume: StructuredResume
    template: str
    matched_skills: list[str] = Field(default_factory=list, description="Your skills the job or role asks for")
    suggested_skills: list[str] = Field(
        default_factory=list, description="Skills the job or role asks for that you did not list; add only real ones"
    )
    notes: list[str] = Field(default_factory=list, description="Tips to make the generated resume stronger")


class ProjectIdeasRequest(BaseModel):
    """What a student wants to become and already knows, to suggest portfolio projects."""

    target_role: str = Field("", max_length=80)
    skills: list[str] = Field(default_factory=list, max_length=80)
    job_description: str = Field("", max_length=20_000)


class ProjectIdeasResponse(BaseModel):
    projects: list[ProjectPick] = Field(default_factory=list)
