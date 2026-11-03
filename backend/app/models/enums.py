import enum


class UserRole(str, enum.Enum):
    driver = "driver"
    operator = "operator"
    admin = "admin"


class StationStatus(str, enum.Enum):
    available = "available"
    vehicle_connected = "vehicle_connected"
    awaiting_payment = "awaiting_payment"
    preparing = "preparing"
    charging = "charging"
    suspended_ev = "suspended_ev"
    finishing = "finishing"
    unavailable = "unavailable"
    faulted = "faulted"
    offline = "offline"
    emergency_stop = "emergency_stop"


class ConnectorType(str, enum.Enum):
    type2 = "type2"
    ccs2 = "ccs2"
    chademo = "chademo"
    gbt_dc = "gbt_dc"
    gbt_ac = "gbt_ac"
    schuko = "schuko"

class SessionStatus(str, enum.Enum):
    awaiting_payment = "awaiting_payment"
    preparing = "preparing"
    charging = "charging"
    suspended_ev = "suspended_ev"
    finishing = "finishing"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


class StopReason(str, enum.Enum):
    user = "user"
    limit_reached = "limit_reached"
    vehicle = "vehicle"
    fault = "fault"
    connection_lost = "connection_lost"
    emergency = "emergency"


class LimitType(str, enum.Enum):
    kwh = "kwh"
    rub = "rub"
    minutes = "minutes"
    until_stop = "until_stop"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class PaymentMethod(str, enum.Enum):
    sbp_qr = "sbp_qr"
    sbp_deeplink = "sbp_deeplink"
    card = "card"
    balance = "balance"


class BookingStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class CommandType(str, enum.Enum):
    start = "start"
    stop = "stop"
    reboot = "reboot"
    lock = "lock"
    unlock = "unlock"
    update_limits = "update_limits"


class CommandStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    completed = "completed"
    failed = "failed"


class ModerationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class TicketStatus(str, enum.Enum):
    open = "open"
    answered = "answered"
    closed = "closed"
