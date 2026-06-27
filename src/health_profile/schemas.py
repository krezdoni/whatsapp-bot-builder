"""Pydantic schemas for health profile data (decrypted view)."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class Condition(BaseModel):
    name: str
    icd_code: str | None = None
    onset_date: str | None = None
    status: str = "active"
    source: str = "user"


class Medication(BaseModel):
    name: str
    dose: str | None = None
    frequency: str | None = None
    started: str | None = None
    prescriber: str | None = None
    active: bool = True


class Allergy(BaseModel):
    substance: str
    reaction: str | None = None
    severity: str | None = None


class Provider(BaseModel):
    name: str
    specialty: str | None = None
    phone: str | None = None
    address: str | None = None


class Vaccination(BaseModel):
    vaccine: str
    date: str | None = None
    lot: str | None = None


class LabResult(BaseModel):
    test: str
    value: str
    unit: str | None = None
    reference_range: str | None = None
    date: str
    lab: str | None = None
    flag: str | None = None


class Appointment(BaseModel):
    title: str
    provider: str | None = None
    date: str
    location: str | None = None
    notes: str | None = None


class HealthProfileData(BaseModel):
    conditions: list[Condition] = []
    medications: list[Medication] = []
    allergies: list[Allergy] = []
    providers: list[Provider] = []
    vaccinations: list[Vaccination] = []
    lab_history: list[LabResult] = []
    appointments: list[Appointment] = []
    notes: list[str] = []


class HealthProfileResponse(BaseModel):
    user_id: str
    profile: HealthProfileData
    fhir_last_synced_at: datetime | None
    updated_at: datetime


class HealthProfileUpdate(BaseModel):
    conditions: list[Condition] | None = None
    medications: list[Medication] | None = None
    allergies: list[Allergy] | None = None
    providers: list[Provider] | None = None
    vaccinations: list[Vaccination] | None = None
    lab_history: list[LabResult] | None = None
    appointments: list[Appointment] | None = None
    notes: list[str] | None = None
