from enum import Enum


class OrderStatus(str, Enum):
    PENDING_RECEIVE = "pending_receive"
    RECEIVED = "received"
    PROCESSING = "processing"
    PENDING_INSPECTION = "pending_inspection"
    PENDING_PICKUP = "pending_pickup"
    COMPLETED = "completed"
    RETURN_PROCESSING = "return_processing"
    SUSPENDED = "suspended"


class SuspendReason(str, Enum):
    CUSTOMER_SUPPLEMENT = "customer_supplement"
    CLOTHES_DAMAGE = "clothes_damage"
    PRICE_DISPUTE = "price_dispute"
    POSTPONE = "postpone"
    OTHER = "other"


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    INSPECTOR = "inspector"


STATUS_LABELS = {
    OrderStatus.PENDING_RECEIVE: "待收件",
    OrderStatus.RECEIVED: "已收件",
    OrderStatus.PROCESSING: "处理中",
    OrderStatus.PENDING_INSPECTION: "待质检",
    OrderStatus.PENDING_PICKUP: "待取件",
    OrderStatus.COMPLETED: "已完成",
    OrderStatus.RETURN_PROCESSING: "退回处理中",
    OrderStatus.SUSPENDED: "已挂起",
}

SUSPEND_REASON_LABELS = {
    SuspendReason.CUSTOMER_SUPPLEMENT: "客户补充说明",
    SuspendReason.CLOTHES_DAMAGE: "衣物破损待确认",
    SuspendReason.PRICE_DISPUTE: "价格争议",
    SuspendReason.POSTPONE: "暂缓处理",
    SuspendReason.OTHER: "其他",
}
