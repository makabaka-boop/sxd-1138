from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.auth import require_admin, get_current_active_user
from app.models import Store, ServiceItem, User, EmployeeSchedule, Order, OrderStatusLog
from app.schemas import (
    StoreCreate, StoreUpdate, StoreResponse,
    ServiceItemCreate, ServiceItemUpdate, ServiceItemResponse,
    UserCreate, UserUpdate, UserResponse,
    EmployeeScheduleCreate, EmployeeScheduleUpdate, EmployeeScheduleResponse,
    OrderResponse
)
from app.enums import OrderStatus
from app.auth import get_password_hash
from app.logger import logger

router = APIRouter(prefix="/admin", tags=["管理员接口"])


@router.post("/stores", response_model=StoreResponse, summary="创建门店")
async def create_store(
    store_data: StoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    store = Store(**store_data.model_dump())
    db.add(store)
    db.commit()
    db.refresh(store)
    logger.info(f"管理员 {current_user.username} 创建门店: {store.name}")
    return store


@router.get("/stores", response_model=List[StoreResponse], summary="获取门店列表")
async def get_stores(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    stores = db.query(Store).offset(skip).limit(limit).all()
    return stores


@router.get("/stores/{store_id}", response_model=StoreResponse, summary="获取门店详情")
async def get_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    return store


@router.put("/stores/{store_id}", response_model=StoreResponse, summary="更新门店信息")
async def update_store(
    store_id: int,
    store_data: StoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    update_data = store_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(store, key, value)
    db.commit()
    db.refresh(store)
    logger.info(f"管理员 {current_user.username} 更新门店: {store.name}")
    return store


@router.delete("/stores/{store_id}", summary="删除门店")
async def delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    store.is_active = False
    db.commit()
    logger.info(f"管理员 {current_user.username} 删除门店: {store.name}")
    return {"message": "门店已删除"}


@router.post("/services", response_model=ServiceItemResponse, summary="创建服务项目")
async def create_service(
    service_data: ServiceItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service = ServiceItem(**service_data.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    logger.info(f"管理员 {current_user.username} 创建服务项目: {service.name}")
    return service


@router.get("/services", response_model=List[ServiceItemResponse], summary="获取服务项目列表")
async def get_services(
    skip: int = 0,
    limit: int = 100,
    store_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(ServiceItem)
    if store_id:
        query = query.filter(ServiceItem.store_id == store_id)
    services = query.offset(skip).limit(limit).all()
    return services


@router.put("/services/{service_id}", response_model=ServiceItemResponse, summary="更新服务项目")
async def update_service(
    service_id: int,
    service_data: ServiceItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service = db.query(ServiceItem).filter(ServiceItem.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务项目不存在")
    update_data = service_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    logger.info(f"管理员 {current_user.username} 更新服务项目: {service.name}")
    return service


@router.delete("/services/{service_id}", summary="删除服务项目")
async def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service = db.query(ServiceItem).filter(ServiceItem.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务项目不存在")
    service.is_active = False
    db.commit()
    logger.info(f"管理员 {current_user.username} 删除服务项目: {service.name}")
    return {"message": "服务项目已删除"}


@router.post("/users", response_model=UserResponse, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.model_dump()
    user_dict.pop("password")
    user = User(**user_dict, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"管理员 {current_user.username} 创建用户: {user.username} ({user.role})")
    return user


@router.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    store_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(User).filter(User.is_active == True)
    if role:
        query = query.filter(User.role == role)
    if store_id:
        query = query.filter(User.store_id == store_id)
    users = query.offset(skip).limit(limit).all()
    return users


@router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    logger.info(f"管理员 {current_user.username} 更新用户: {user.username}")
    return user


@router.post("/schedules", response_model=EmployeeScheduleResponse, summary="创建员工排班")
async def create_schedule(
    schedule_data: EmployeeScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    employee = db.query(User).filter(User.id == schedule_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    schedule = EmployeeSchedule(**schedule_data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    logger.info(f"管理员 {current_user.username} 创建排班: 员工 {employee.username} 日期 {schedule.work_date}")
    return schedule


@router.get("/schedules", response_model=List[EmployeeScheduleResponse], summary="获取排班列表")
async def get_schedules(
    employee_id: int = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(EmployeeSchedule)
    if employee_id:
        query = query.filter(EmployeeSchedule.employee_id == employee_id)
    if start_date:
        query = query.filter(EmployeeSchedule.work_date >= start_date)
    if end_date:
        query = query.filter(EmployeeSchedule.work_date <= end_date)
    schedules = query.order_by(EmployeeSchedule.work_date).all()
    return schedules


@router.put("/schedules/{schedule_id}", response_model=EmployeeScheduleResponse, summary="更新排班")
async def update_schedule(
    schedule_id: int,
    schedule_data: EmployeeScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    schedule = db.query(EmployeeSchedule).filter(EmployeeSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="排班不存在")
    update_data = schedule_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)
    db.commit()
    db.refresh(schedule)
    logger.info(f"管理员 {current_user.username} 更新排班 ID: {schedule_id}")
    return schedule


@router.delete("/schedules/{schedule_id}", summary="删除排班")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    schedule = db.query(EmployeeSchedule).filter(EmployeeSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="排班不存在")
    db.delete(schedule)
    db.commit()
    logger.info(f"管理员 {current_user.username} 删除排班 ID: {schedule_id}")
    return {"message": "排班已删除"}


def convert_admin_order_to_response(order: Order) -> dict:
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
            "log_type": log.log_type,
            "suspend_reason": log.suspend_reason,
            "resume_result": log.resume_result,
            "urgent_changed": log.urgent_changed or False,
            "from_urgent": log.from_urgent or False,
            "to_urgent": log.to_urgent or False,
            "urgent_remark_changed": log.urgent_remark_changed or False,
            "from_urgent_remark": log.from_urgent_remark,
            "to_urgent_remark": log.to_urgent_remark,
            "created_at": log.created_at
        })

    suspended_by_name = order.suspended_by_user.full_name if order.suspended_by_user else None

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
        "is_suspended": order.is_suspended or False,
        "previous_status": order.previous_status,
        "suspend_reason": order.suspend_reason,
        "suspend_remark": order.suspend_remark,
        "suspended_by": order.suspended_by,
        "suspended_at": order.suspended_at,
        "suspended_by_name": suspended_by_name,
        "is_urgent": order.is_urgent or False,
        "urgent_remark": order.urgent_remark,
        "urgent_fee": order.urgent_fee or 0.0,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": items,
        "status_logs": status_logs
    }


@router.get("/orders", response_model=List[OrderResponse], summary="管理员获取订单列表（支持异常筛选）")
async def admin_get_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    store_id: Optional[int] = None,
    keyword: Optional[str] = None,
    is_suspended: Optional[bool] = None,
    is_urgent: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(Order).options(
        joinedload(Order.items),
        joinedload(Order.status_logs).joinedload(OrderStatusLog.operator),
        joinedload(Order.suspended_by_user)
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
    if is_suspended is not None:
        query = query.filter(Order.is_suspended == is_suspended)
    if is_urgent is not None:
        query = query.filter(Order.is_urgent == is_urgent)
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [convert_admin_order_to_response(o) for o in orders]


@router.get("/orders/suspended", response_model=List[OrderResponse], summary="获取所有挂起的异常订单")
async def admin_get_suspended_orders(
    skip: int = 0,
    limit: int = 100,
    store_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    query = db.query(Order).options(
        joinedload(Order.items),
        joinedload(Order.status_logs).joinedload(OrderStatusLog.operator),
        joinedload(Order.suspended_by_user)
    ).filter(Order.is_suspended == True)
    if store_id:
        query = query.filter(Order.store_id == store_id)
    orders = query.order_by(Order.suspended_at.desc()).offset(skip).limit(limit).all()
    return [convert_admin_order_to_response(o) for o in orders]
