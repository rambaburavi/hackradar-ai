from enum import StrEnum


class EventCategory(StrEnum):
    HACKATHON = "hackathon"
    CODING_COMPETITION = "coding_competition"
    AI_CHALLENGE = "ai_challenge"
    DATA_SCIENCE = "data_science"
    CAPTURE_THE_FLAG = "capture_the_flag"
    INNOVATION_CHALLENGE = "innovation_challenge"
    STARTUP_COMPETITION = "startup_competition"
    ROBOTICS = "robotics"
    TECH_CONFERENCE = "tech_conference"
    WORKSHOP = "workshop"
    OTHER = "other"
    UNKNOWN = "unknown"


class ParticipationMode(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class EventLifecycleStatus(StrEnum):
    UPCOMING = "upcoming"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    PARTIALLY_VERIFIED = "partially_verified"
    VERIFIED = "verified"
    CONFLICTING = "conflicting"
    SOURCE_UNAVAILABLE = "source_unavailable"


class DiscoveryRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ExtractionMethod(StrEnum):
    API = "api"
    JSON_LD = "json_ld"
    HTML = "html"
    RSS = "rss"
    LLM = "llm"
    MANUAL = "manual"


class ExtractionStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class EligibilityStatus(StrEnum):
    ELIGIBLE = "eligible"
    POTENTIALLY_ELIGIBLE = "potentially_eligible"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"


class SourceHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"