from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from app.enums import OrderStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    store_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    store_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StoreBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    manager: Optional[str] = None


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    manager: Optional[str] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    duration_minutes: Optional[int] = None
    store_id: int


class ServiceItemCreate(ServiceItemBase):
    pass


class ServiceItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_minutes: Optional[int] = None
    store_id: Optional[int] = None
    is_active: Optional[bool] = None


class ServiceItemResponse(ServiceItemBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeScheduleBase(BaseModel):
    employee_id: int
    work_date: date
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None
    note: Optional[str] = None


class EmployeeScheduleCreate(EmployeeScheduleBase):
    pass


class EmployeeScheduleUpdate(BaseModel):
    work_date: Optional[date] = None
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None
    note: Optional[str] = None


class EmployeeScheduleResponse(EmployeeScheduleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    service_item_id: int
    service_name: str
    quantity: int = 1
    unit_price: float
    subtotal: float
    remark: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_name: str
    customer_phone: str
    store_id: int
    remark: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    remark: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    target_status: OrderStatus
    remark: Optional[str] = None


class OrderStatusLogResponse(BaseModel):
    id: int
    order_id: int
    from_status: Optional[str]
    to_status: str
    operator_id: Optional[int]
    operator_name: Optional[str]
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderResponse(OrderBase):
    id: int
    order_no: str
    status: OrderStatus
    total_amount: float
    pickup_code: Optional[str]
    operator_id: Optional[int]
    inspector_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    status_logs: List[OrderStatusLogResponse] = []

    class Config:
        from_attributes = True


class AvailableTransitionsResponse(BaseModel):
    current_status: OrderStatus
    forward: List[OrderStatus]
    rollback: List[OrderStatus]
