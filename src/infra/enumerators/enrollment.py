from enum import Enum


class EnrollmentStatus(str, Enum):
    """Enumeration for enrollment status values.

    Represents the possible states of an enrollment throughout its lifecycle.
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
