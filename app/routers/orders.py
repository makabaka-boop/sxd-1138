from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
import random
import string
from app.database import get_db
from app.auth import require_operator, require_inspector, require_any_staff, get_current_active_user
from app.models import Order, OrderItem, OrderStatusLog, User, Store
from app.schemas import (
    OrderCreate, OrderUpdate, OrderResponse,
    OrderStatusUpdate, OrderStatusLogResponse,
    AvailableTransitionsResponse
)
from app.enums import OrderStatus, STATUS_LABELS, UserRole
from app.state_machine import OrderStateMachine, StateTransitionError
from app.logger import logger

router = APIRouter(prefix="/orders", tags=["订单管理"])


def generate_order_no() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"LD{timestamp}{random_str}"


def generate_pickup_code() -> str:
    return ''.join(random.choices(string.digits, k=6))


def create_status_log(
    db: Session,
    order_id: int,
    from_status: Optional[str],
    to_status: str,
    operator_id: int,
    remark: Optional[str] = None
):
    log = OrderStatusLog(
        order_id=order_id,
        from_status=from_status,
        to_status=to_status,
        operator_id=operator_id,
        remark=remark
    )
    db.add(log)
    return log


def convert_order_to_response(order: Order) -> dict:
    items = []
    for item in order.items:
        items.append({
            "id": item.id,
            "service_item_id": item.service_item_id,
            "service_name": item.service_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": item.subtotal,
            "remark": item.remark,
            "created_at": item.created_at
        })

    status_logs = []
    for log in order.status_logs:
        operator_name = log.operator.full_name if log.operator else None
        status_logs.append({
            "id": log.id,
            "order_id": log.order_id,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "operator_id": log.operator_id,
            "operator_name": operator_name,
            "remark": log.remark,
            "created_at": log.created_at
        })

    return {
        "id": order.id,
        "order_no": order.order_no,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "store_id": order.store_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "pickup_code": order.pickup_code,
        "remark": order.remark,
        "operator_id": order.operator_id,
        "inspector_id": order.inspector_id,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": items,
        "status_logs": status_logs
    }


def get_order_with_relations(db: Session, order_id: int) -> Optional[Order]:
    return db.query(Order).options(
        joinedload(Order.items),
        joinedload(Order.status_logs).joinedload(OrderStatusLog.operator)
    ).filter(Order.id == order_id).first()


@router.post("", response_model=OrderResponse, summary="创建订单（操作员登记收件）")
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    store = db.query(Store).filter(Store.id == order_data.store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")

    order_no = generate_order_no()
    pickup_code = generate_pickup_code()
    total_amount = sum(item.subtotal for item in order_data.items)

    order = Order(
        order_no=order_no,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        store_id=order_data.store_id,
        status=OrderStatus.PENDING_RECEIVE,
        total_amount=total_amount,
        pickup_code=pickup_code,
        remark=order_data.remark,
        operator_id=current_user.id
    )
    db.add(order)
    db.flush()

    for item_data in order_data.items:
        item = OrderItem(
            order_id=order.id,
            service_item_id=item_data.service_item_id,
            service_name=item_data.service_name,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            subtotal=item_data.subtotal,
            remark=item_data.remark
        )
        db.add(item)

    create_status_log(
        db=db,
        order_id=order.id,
        from_status=None,
        to_status=OrderStatus.PENDING_RECEIVE,
        operator_id=current_user.id,
        remark="订单创建"
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(f"操作员 {current_user.username} 创建订单 {order_no}")
    return convert_order_to_response(order_full)


@router.get("", response_model=List[OrderResponse], summary="获取订单列表")
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    store_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    query = db.query(Order).options(
        joinedload(Order.items),
        joinedload(Order.status_logs).joinedload(OrderStatusLog.operator)
    )
    if status:
        query = query.filter(Order.status == status)
    if store_id:
        query = query.filter(Order.store_id == store_id)
    if keyword:
        query = query.filter(
            (Order.order_no.contains(keyword)) |
            (Order.customer_name.contains(keyword)) |
            (Order.customer_phone.contains(keyword))
        )
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [convert_order_to_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse, summary="获取订单详情")
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    order = get_order_with_relations(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return convert_order_to_response(order)


@router.put("/{order_id}", response_model=OrderResponse, summary="更新订单基本信息")
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == OrderStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="订单已完成，不可修改")

    update_data = order_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(f"操作员 {current_user.username} 更新订单 {order.order_no}")
    return convert_order_to_response(order_full)


@router.get("/{order_id}/transitions", response_model=AvailableTransitionsResponse, summary="获取订单可流转状态")
async def get_available_transitions(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    transitions = OrderStateMachine.get_available_transitions(OrderStatus(order.status))
    return {
        "current_status": order.status,
        "forward": transitions["forward"],
        "rollback": transitions["rollback"]
    }


INSPECTOR_ALLOWED_STATUSES = [
    OrderStatus.PENDING_INSPECTION,
    OrderStatus.RETURN_PROCESSING,
    OrderStatus.PENDING_PICKUP,
]

OPERATOR_ALLOWED_STATUSES = [
    OrderStatus.PENDING_RECEIVE,
    OrderStatus.RECEIVED,
    OrderStatus.PROCESSING,
    OrderStatus.RETURN_PROCESSING,
]


@router.post("/{order_id}/status", response_model=OrderResponse, summary="更新订单状态")
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    current_status = OrderStatus(order.status)
    target_status = status_data.target_status

    if current_user.role == UserRole.INSPECTOR:
        if current_status not in INSPECTOR_ALLOWED_STATUSES:
            raise HTTPException(
                status_code=403,
                detail=f"审核员只能处理质检阶段的订单，当前状态为 {STATUS_LABELS.get(current_status)}"
            )

    if current_user.role == UserRole.OPERATOR:
        if target_status in [OrderStatus.PENDING_PICKUP, OrderStatus.COMPLETED, OrderStatus.RETURN_PROCESSING]:
            raise HTTPException(status_code=403, detail="操作员无权执行质检或取件确认操作")

    if target_status in [OrderStatus.PENDING_PICKUP, OrderStatus.COMPLETED]:
        if current_user.role not in [UserRole.ADMIN, UserRole.INSPECTOR]:
            raise HTTPException(status_code=403, detail="只有审核员可以执行质检通过或确认取件")

    if target_status == OrderStatus.RETURN_PROCESSING:
        if current_user.role not in [UserRole.ADMIN, UserRole.INSPECTOR]:
            raise HTTPException(status_code=403, detail="只有审核员可以执行质检退回")

    try:
        OrderStateMachine.validate_transition(current_status, target_status)
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)

    from_status = order.status
    order.status = target_status

    if target_status == OrderStatus.PENDING_PICKUP:
        order.inspector_id = current_user.id
    if target_status == OrderStatus.COMPLETED:
        order.inspector_id = current_user.id

    is_rollback = OrderStateMachine.is_rollback_transition(current_status, target_status)
    transition_type = "回退" if is_rollback else "流转"

    remark = status_data.remark or f"{transition_type}: {STATUS_LABELS.get(current_status)} -> {STATUS_LABELS.get(target_status)}"
    create_status_log(
        db=db,
        order_id=order.id,
        from_status=from_status,
        to_status=target_status,
        operator_id=current_user.id,
        remark=remark
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(
        f"用户 {current_user.username} 将订单 {order.order_no} 状态从 {from_status} "
        f"{transition_type} 为 {target_status}"
    )
    return convert_order_to_response(order_full)


@router.post("/{order_id}/receive", response_model=OrderResponse, summary="确认收件（操作员）")
async def receive_order(
    order_id: int,
    remark: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    current_status = OrderStatus(order.status)
    target_status = OrderStatus.RECEIVED

    try:
        OrderStateMachine.validate_transition(current_status, target_status)
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)

    from_status = order.status
    order.status = target_status
    order.operator_id = current_user.id

    create_status_log(
        db=db,
        order_id=order.id,
        from_status=from_status,
        to_status=target_status,
        operator_id=current_user.id,
        remark=remark or "确认收件"
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(f"操作员 {current_user.username} 确认收件: 订单 {order.order_no}")
    return convert_order_to_response(order_full)


@router.post("/{order_id}/process", response_model=OrderResponse, summary="开始处理（操作员）")
async def process_order(
    order_id: int,
    remark: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    current_status = OrderStatus(order.status)
    target_status = OrderStatus.PROCESSING

    try:
        OrderStateMachine.validate_transition(current_status, target_status)
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)

    from_status = order.status
    order.status = target_status

    create_status_log(
        db=db,
        order_id=order.id,
        from_status=from_status,
        to_status=target_status,
        operator_id=current_user.id,
        remark=remark or "开始处理"
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(f"操作员 {current_user.username} 开始处理: 订单 {order.order_no}")
    return convert_order_to_response(order_full)


@router.post("/{order_id}/reprocess", response_model=OrderResponse, summary="退回后重新处理（操作员）")
async def reprocess_order(
    order_id: int,
    remark: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    current_status = OrderStatus(order.status)
    target_status = OrderStatus.PROCESSING

    try:
        OrderStateMachine.validate_transition(current_status, target_status)
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)

    from_status = order.status
    order.status = target_status

    create_status_log(
        db=db,
        order_id=order.id,
        from_status=from_status,
        to_status=target_status,
        operator_id=current_user.id,
        remark=remark or "退回后重新处理"
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(f"操作员 {current_user.username} 退回后重新处理: 订单 {order.order_no}")
    return convert_order_to_response(order_full)


@router.post("/{order_id}/to-inspection", response_model=OrderResponse, summary="提交质检（操作员）")
async def send_to_inspection(
    order_id: int,
    remark: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    current_status = OrderStatus(order.status)
    target_status = OrderStatus.PENDING_INSPECTION

    try:
        OrderStateMachine.validate_transition(current_status, target_status)
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)

    from_status = order.status
    order.status = target_status

    create_status_log(
        db=db,
        order_id=order.id,
        from_status=from_status,
        to_status=target_status,
        operator_id=current_user.id,
        remark=remark or "提交质检"
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(f"操作员 {current_user.username} 提交质检: 订单 {order.order_no}")
    return convert_order_to_response(order_full)


@router.post("/{order_id}/inspect-pass", response_model=OrderResponse, summary="质检通过（审核员）")
async def inspect_pass(
    order_id: int,
    remark: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    current_status = OrderStatus(order.status)
    target_status = OrderStatus.PENDING_PICKUP

    try:
        OrderStateMachine.validate_transition(current_status, target_status)
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)

    from_status = order.status
    order.status = target_status
    order.inspector_id = current_user.id

    create_status_log(
        db=db,
        order_id=order.id,
        from_status=from_status,
        to_status=target_status,
        operator_id=current_user.id,
        remark=remark or "质检通过，待取件"
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(f"审核员 {current_user.username} 质检通过: 订单 {order.order_no}，通知客户取件")
    return convert_order_to_response(order_full)


@router.post("/{order_id}/inspect-reject", response_model=OrderResponse, summary="质检退回（审核员）")
async def inspect_reject(
    order_id: int,
    remark: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    current_status = OrderStatus(order.status)
    target_status = OrderStatus.RETURN_PROCESSING

    try:
        OrderStateMachine.validate_transition(current_status, target_status)
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)

    from_status = order.status
    order.status = target_status
    order.inspector_id = current_user.id

    create_status_log(
        db=db,
        order_id=order.id,
        from_status=from_status,
        to_status=target_status,
        operator_id=current_user.id,
        remark=remark or "质检不合格，退回处理"
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.warning(f"审核员 {current_user.username} 质检退回: 订单 {order.order_no} - {remark}")
    return convert_order_to_response(order_full)


@router.post("/{order_id}/complete", response_model=OrderResponse, summary="确认取件完成（审核员）")
async def complete_order(
    order_id: int,
    remark: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    current_status = OrderStatus(order.status)
    target_status = OrderStatus.COMPLETED

    try:
        OrderStateMachine.validate_transition(current_status, target_status)
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)

    from_status = order.status
    order.status = target_status

    create_status_log(
        db=db,
        order_id=order.id,
        from_status=from_status,
        to_status=target_status,
        operator_id=current_user.id,
        remark=remark or "客户已取件，订单完成"
    )

    db.commit()
    order_full = get_order_with_relations(db, order.id)
    logger.info(f"审核员 {current_user.username} 确认取件完成: 订单 {order.order_no}")
    return convert_order_to_response(order_full)


@router.get("/{order_id}/logs", response_model=List[OrderStatusLogResponse], summary="获取订单状态流转日志")
async def get_order_logs(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    logs = db.query(OrderStatusLog).options(
        joinedload(OrderStatusLog.operator)
    ).filter(OrderStatusLog.order_id == order_id).order_by(OrderStatusLog.created_at).all()

    result = []
    for log in logs:
        operator_name = log.operator.full_name if log.operator else None
        result.append({
            "id": log.id,
            "order_id": log.order_id,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "operator_id": log.operator_id,
            "operator_name": operator_name,
            "remark": log.remark,
            "created_at": log.created_at
        })

    return result


@router.post("/{order_id}/notify", summary="发送取件通知")
async def send_pickup_notification(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != OrderStatus.PENDING_PICKUP:
        raise HTTPException(status_code=400, detail="订单未处于待取件状态")

    logger.info(f"发送取件通知: 订单 {order.order_no}，客户 {order.customer_name}，电话 {order.customer_phone}，取件码 {order.pickup_code}")

    return {
        "message": "取件通知已发送",
        "order_no": order.order_no,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "pickup_code": order.pickup_code
    }
