from app.models.event import Event, event_tag_link
from app.models.discovery_source import DiscoverySource
from app.models.event_source import EventSource
from app.models.event_tag import EventTag
from app.models.eligibility_criteria import EligibilityCriteria
from app.models.discovery_run import DiscoveryRun
from app.models.verification_log import VerificationLog
from app.models.extraction_record import ExtractionRecord

# Configure relationships after all models are imported.
from app.models import relationships as _relationships


__all__ = [
    "Event",
    "DiscoverySource",
    "EventSource",
    "EventTag",
    "EligibilityCriteria",
    "DiscoveryRun",
    "VerificationLog",
    "ExtractionRecord",
    "event_tag_link",
]