from sqlalchemy.orm import relationship

from app.models.event import Event, event_tag_link
from app.models.event_source import EventSource
from app.models.discovery_source import DiscoverySource
from app.models.event_tag import EventTag
from app.models.eligibility_criteria import EligibilityCriteria
from app.models.discovery_run import DiscoveryRun
from app.models.verification_log import VerificationLog
from app.models.extraction_record import ExtractionRecord


# Event <-> EventSource
# One-to-many

Event.sources = relationship(
    EventSource,
    back_populates="event",
    cascade="all, delete-orphan",
    passive_deletes=True,
)

EventSource.event = relationship(
    Event,
    back_populates="sources",
)


# DiscoverySource <-> EventSource
# One-to-many

DiscoverySource.event_sources = relationship(
    EventSource,
    back_populates="discovery_source",
    passive_deletes="all",
)

EventSource.discovery_source = relationship(
    DiscoverySource,
    back_populates="event_sources",
)


# Event <-> EligibilityCriteria
# One-to-one

Event.eligibility = relationship(
    EligibilityCriteria,
    back_populates="event",
    cascade="all, delete-orphan",
    single_parent=True,
    uselist=False,
    passive_deletes=True,
)

EligibilityCriteria.event = relationship(
    Event,
    back_populates="eligibility",
)


# Event <-> EventTag
# Many-to-many

Event.tags = relationship(
    EventTag,
    secondary=event_tag_link,
    back_populates="events",
    passive_deletes=True,
)

EventTag.events = relationship(
    Event,
    secondary=event_tag_link,
    back_populates="tags",
    passive_deletes=True,
)


# DiscoverySource <-> DiscoveryRun
# One-to-many

DiscoverySource.discovery_runs = relationship(
    DiscoveryRun,
    back_populates="source",
    passive_deletes="all",
)

DiscoveryRun.source = relationship(
    DiscoverySource,
    back_populates="discovery_runs",
)


# Event <-> VerificationLog
# One-to-many

Event.verification_logs = relationship(
    VerificationLog,
    back_populates="event",
    cascade="all, delete-orphan",
    passive_deletes=True,
)

VerificationLog.event = relationship(
    Event,
    back_populates="verification_logs",
)


# EventSource <-> VerificationLog
# One-to-many

EventSource.verification_logs = relationship(
    VerificationLog,
    back_populates="source",
    passive_deletes=True,
)

VerificationLog.source = relationship(
    EventSource,
    back_populates="verification_logs",
)


# Event <-> ExtractionRecord
# One-to-many

Event.extraction_records = relationship(
    ExtractionRecord,
    back_populates="event",
    cascade="all, delete",
    passive_deletes=True,
)

ExtractionRecord.event = relationship(
    Event,
    back_populates="extraction_records",
)


# EventSource <-> ExtractionRecord
# One-to-many

EventSource.extraction_records = relationship(
    ExtractionRecord,
    back_populates="source",
    passive_deletes=True,
)

ExtractionRecord.source = relationship(
    EventSource,
    back_populates="extraction_records",
)


# DiscoveryRun <-> ExtractionRecord
# One-to-many

DiscoveryRun.extraction_records = relationship(
    ExtractionRecord,
    back_populates="discovery_run",
    passive_deletes=True,
)

ExtractionRecord.discovery_run = relationship(
    DiscoveryRun,
    back_populates="extraction_records",
)