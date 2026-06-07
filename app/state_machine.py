from typing import Dict, List, Optional
from app.enums import OrderStatus, STATUS_LABELS
from app.logger import logger


class StateTransitionError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class OrderStateMachine:
    NORMAL_TRANSITIONS: Dict[OrderStatus, List[OrderStatus]] = {
        OrderStatus.PENDING_RECEIVE: [OrderStatus.RECEIVED],
        OrderStatus.RECEIVED: [OrderStatus.PROCESSING],
        OrderStatus.PROCESSING: [OrderStatus.PENDING_INSPECTION],
        OrderStatus.PENDING_INSPECTION: [OrderStatus.PENDING_PICKUP, OrderStatus.RETURN_PROCESSING],
        OrderStatus.RETURN_PROCESSING: [OrderStatus.PROCESSING],
        OrderStatus.PENDING_PICKUP: [OrderStatus.COMPLETED],
        OrderStatus.COMPLETED: [],
    }

    ALLOWED_ROLLBACKS: Dict[OrderStatus, List[OrderStatus]] = {
        OrderStatus.RECEIVED: [OrderStatus.PENDING_RECEIVE],
        OrderStatus.PROCESSING: [OrderStatus.RECEIVED],
        OrderStatus.PENDING_INSPECTION: [OrderStatus.PROCESSING],
        OrderStatus.RETURN_PROCESSING: [OrderStatus.PENDING_INSPECTION],
        OrderStatus.PENDING_PICKUP: [OrderStatus.PENDING_INSPECTION],
        OrderStatus.COMPLETED: [],
    }

    TERMINAL_STATES = {OrderStatus.COMPLETED}

    @classmethod
    def can_transition(cls, current_status: OrderStatus, target_status: OrderStatus) -> bool:
        if current_status in cls.TERMINAL_STATES:
            return False
        allowed = cls.NORMAL_TRANSITIONS.get(current_status, [])
        return target_status in allowed

    @classmethod
    def can_rollback(cls, current_status: OrderStatus, target_status: OrderStatus) -> bool:
        if current_status in cls.TERMINAL_STATES:
            return False
        allowed = cls.ALLOWED_ROLLBACKS.get(current_status, [])
        return target_status in allowed

    @classmethod
    def validate_transition(cls, current_status: OrderStatus, target_status: OrderStatus) -> None:
        if current_status == target_status:
            raise StateTransitionError(f"订单状态已是 {STATUS_LABELS.get(target_status, target_status)}，无需变更")

        if current_status in cls.TERMINAL_STATES:
            raise StateTransitionError(
                f"订单已处于终态 {STATUS_LABELS.get(current_status, current_status)}，不可变更"
            )

        is_normal = cls.can_transition(current_status, target_status)
        is_rollback = cls.can_rollback(current_status, target_status)

        if not is_normal and not is_rollback:
            raise StateTransitionError(
                f"不允许从 {STATUS_LABELS.get(current_status, current_status)} "
                f"变更为 {STATUS_LABELS.get(target_status, target_status)}"
            )

    @classmethod
    def get_available_transitions(cls, current_status: OrderStatus) -> Dict[str, List[OrderStatus]]:
        return {
            "forward": cls.NORMAL_TRANSITIONS.get(current_status, []),
            "rollback": cls.ALLOWED_ROLLBACKS.get(current_status, []),
        }

    @classmethod
    def is_rollback_transition(cls, current_status: OrderStatus, target_status: OrderStatus) -> bool:
        return cls.can_rollback(current_status, target_status)
