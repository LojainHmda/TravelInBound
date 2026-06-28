"""
Central status definitions.

TWO STATUS LEVELS:
  ServiceStatus  — per-service (hotel, transport, meal, guide)
                   "Confirmed" = supplier sent us confirmation
  RequestStatus  — whole tour file
                   "Confirmed" = customer sent us confirmation
"""


class ServiceStatus:
    REQUEST = 'REQUEST'        # awaiting supplier confirmation
    CONFIRMED = 'CONFIRMED'    # supplier confirmed — deal done
    CANCELLED = 'CANCELLED'    # cancelled with supplier

    ALL = (REQUEST, CONFIRMED, CANCELLED)

    LABELS = {
        REQUEST: 'Requested',
        CONFIRMED: 'Confirmed',
        CANCELLED: 'Cancelled',
    }

    @classmethod
    def label(cls, value: str) -> str:
        return cls.LABELS.get(str(value).upper(), value)


class RequestStatus:
    REQUEST = 'REQUEST'        # initial — customer has not confirmed
    CONFIRMED = 'CONFIRMED'    # customer confirmed the whole tour
    INVOICED = 'INVOICED'      # invoice issued to customer

    # Legacy aliases kept for backwards compatibility
    BOOKED = 'CONFIRMED'
    IN_PROGRESS = 'REQUEST'
    COMPLETED = 'INVOICED'

    ALL = (REQUEST, CONFIRMED, INVOICED)

    LABELS = {
        REQUEST: 'Requested',
        CONFIRMED: 'Confirmed',
        INVOICED: 'Invoiced',
    }

    @classmethod
    def label(cls, value: str) -> str:
        v = str(value).upper()
        # Normalize legacy values
        if v in ('BOOKED', 'IN_PROGRESS', 'PROCESSING', 'QUOTED', 'SUPPLIER_CONFIRMED'):
            v = cls.CONFIRMED
        if v in ('COMPLETED', 'INVOICE'):
            v = cls.INVOICED
        return cls.LABELS.get(v, value)

    @classmethod
    def normalize(cls, value: str) -> str:
        """Convert legacy status string to canonical value."""
        v = str(value).upper()
        if v in ('BOOKED', 'IN_PROGRESS', 'PROCESSING', 'QUOTED', 'SUPPLIER_CONFIRMED'):
            return cls.CONFIRMED
        if v in ('COMPLETED', 'INVOICE'):
            return cls.INVOICED
        return v if v in cls.ALL else cls.REQUEST
