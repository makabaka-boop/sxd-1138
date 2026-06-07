from enum import Enum


class OrderStatus(str, Enum):
    PENDING_RECEIVE = "pending_receive"
    RECEIVED = "received"
    PROCESSING = "processing"
    PENDING_INSPECTION = "pending_inspection"
    PENDING_PICKUP = "pending_pickup"
    COMPLETED = "completed"
    RETURN_PROCESSING = "return_processing"


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
}
