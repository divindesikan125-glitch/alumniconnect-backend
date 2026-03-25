from pydantic import BaseModel, Field


class JobAnalytics(BaseModel):
    total_jobs: int = Field(ge=0)
    total_applications: int = Field(ge=0)
    accepted: int = Field(ge=0)
    rejected: int = Field(ge=0)
    pending: int = Field(ge=0)


class EventAnalytics(BaseModel):
    total_events: int = Field(ge=0)
    total_registrations: int = Field(ge=0)
    upcoming_events: int = Field(ge=0)


class InstitutionDashboardResponse(BaseModel):
    jobs: JobAnalytics
    events: EventAnalytics