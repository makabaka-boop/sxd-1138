from typing import Dict, List, Optional, Set
from app.enums import OrderStatus, STATUS_LABELS, SUSPEND_REASON_LABELS, SuspendReason
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
        OrderStatus.SUSPENDED: [],
    }

    ALLOWED_ROLLBACKS: Dict[OrderStatus, List[OrderStatus]] = {
        OrderStatus.RECEIVED: [OrderStatus.PENDING_RECEIVE],
        OrderStatus.PROCESSING: [OrderStatus.RECEIVED],
        OrderStatus.PENDING_INSPECTION: [OrderStatus.PROCESSING],
        OrderStatus.RETURN_PROCESSING: [OrderStatus.PENDING_INSPECTION],
        OrderStatus.PENDING_PICKUP: [OrderStatus.PENDING_INSPECTION],
        OrderStatus.COMPLETED: [],
        OrderStatus.SUSPENDED: [],
    }

    TERMINAL_STATES = {OrderStatus.COMPLETED}

    SUSPENDABLE_STATES: Set[OrderStatus] = {
        OrderStatus.PENDING_RECEIVE,
        OrderStatus.RECEIVED,
        OrderStatus.PROCESSING,
        OrderStatus.PENDING_INSPECTION,
    }

    @classmethod
    def can_transition(cls, current_status: OrderStatus, target_status: OrderStatus, is_suspended: bool = False) -> bool:
        if is_suspended:
            return False
        if current_status in cls.TERMINAL_STATES:
            return False
        allowed = cls.NORMAL_TRANSITIONS.get(current_status, [])
        return target_status in allowed

    @classmethod
    def can_rollback(cls, current_status: OrderStatus, target_status: OrderStatus, is_suspended: bool = False) -> bool:
        if is_suspended:
            return False
        if current_status in cls.TERMINAL_STATES:
            return False
        allowed = cls.ALLOWED_ROLLBACKS.get(current_status, [])
        return target_status in allowed

    @classmethod
    def can_suspend(cls, current_status: OrderStatus, is_suspended: bool) -> bool:
        if is_suspended:
            return False
        return current_status in cls.SUSPENDABLE_STATES

    @classmethod
    def can_resume(cls, is_suspended: bool) -> bool:
        return is_suspended

    @classmethod
    def validate_transition(cls, current_status: OrderStatus, target_status: OrderStatus, is_suspended: bool = False) -> None:
        if current_status == target_status:
            raise StateTransitionError(f"订单状态已是 {STATUS_LABELS.get(target_status, target_status)}，无需变更")

        if is_suspended:
            raise StateTransitionError("订单已挂起，请先恢复后再进行状态变更")

        if current_status in cls.TERMINAL_STATES:
            raise StateTransitionError(
                f"订单已处于终态 {STATUS_LABELS.get(current_status, current_status)}，不可变更"
            )

        is_normal = cls.can_transition(current_status, target_status, is_suspended)
        is_rollback = cls.can_rollback(current_status, target_status, is_suspended)

        if not is_normal and not is_rollback:
            raise StateTransitionError(
                f"不允许从 {STATUS_LABELS.get(current_status, current_status)} "
                f"变更为 {STATUS_LABELS.get(target_status, target_status)}"
            )

    @classmethod
    def validate_suspend(cls, current_status: OrderStatus, is_suspended: bool) -> None:
        if is_suspended:
            raise StateTransitionError("订单已处于挂起状态")

        if current_status not in cls.SUSPENDABLE_STATES:
            raise StateTransitionError(
                f"当前状态 {STATUS_LABELS.get(current_status, current_status)} 不允许挂起，"
                f"仅待收件、已收件、处理中、待质检阶段可挂起"
            )

    @classmethod
    def validate_resume(cls, is_suspended: bool) -> None:
        if not is_suspended:
            raise StateTransitionError("订单未处于挂起状态，无需恢复")

    @classmethod
    def get_available_transitions(cls, current_status: OrderStatus, is_suspended: bool = False) -> Dict[str, List[OrderStatus]]:
        if is_suspended:
            return {
                "forward": [],
                "rollback": [],
            }
        return {
            "forward": cls.NORMAL_TRANSITIONS.get(current_status, []),
            "rollback": cls.ALLOWED_ROLLBACKS.get(current_status, []),
        }

    @classmethod
    def is_rollback_transition(cls, current_status: OrderStatus, target_status: OrderStatus) -> bool:
        return cls.can_rollback(current_status, target_status)
