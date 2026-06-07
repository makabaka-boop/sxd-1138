from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.enums import OrderStatus, UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)
    phone = Column(String(20))
    store_id = Column(Integer, ForeignKey("stores.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    store = relationship("Store", back_populates="employees")
    schedules = relationship("EmployeeSchedule", back_populates="employee")


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255))
    phone = Column(String(20))
    manager = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    employees = relationship("User", back_populates="store")
    services = relationship("ServiceItem", back_populates="store")
    orders = relationship("Order", back_populates="store")


class ServiceItem(Base):
    __tablename__ = "service_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer)
    store_id = Column(Integer, ForeignKey("stores.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    store = relationship("Store", back_populates="services")


class EmployeeSchedule(Base):
    __tablename__ = "employee_schedules"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"))
    work_date = Column(Date, nullable=False)
    shift_start = Column(String(10))
    shift_end = Column(String(10))
    note = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    employee = relationship("User", back_populates="schedules")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, index=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"))
    status = Column(String(30), default=OrderStatus.PENDING_RECEIVE, nullable=False)
    total_amount = Column(Float, default=0.0)
    pickup_code = Column(String(20))
    remark = Column(Text)
    operator_id = Column(Integer, ForeignKey("users.id"))
    inspector_id = Column(Integer, ForeignKey("users.id"))
    is_suspended = Column(Boolean, default=False)
    previous_status = Column(String(30))
    suspend_reason = Column(String(50))
    suspend_remark = Column(Text)
    suspended_by = Column(Integer, ForeignKey("users.id"))
    suspended_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    store = relationship("Store", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_logs = relationship("OrderStatusLog", back_populates="order", cascade="all, delete-orphan", order_by="OrderStatusLog.id")
    operator = relationship("User", foreign_keys=[operator_id])
    inspector = relationship("User", foreign_keys=[inspector_id])
    suspended_by_user = relationship("User", foreign_keys=[suspended_by])


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    service_item_id = Column(Integer, ForeignKey("service_items.id"))
    service_name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    order = relationship("Order", back_populates="items")
    service_item = relationship("ServiceItem")


class OrderStatusLog(Base):
    __tablename__ = "order_status_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    from_status = Column(String(30))
    to_status = Column(String(30), nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"))
    remark = Column(Text)
    log_type = Column(String(20), default="status_change")
    suspend_reason = Column(String(50))
    resume_result = Column(Text)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    order = relationship("Order", back_populates="status_logs")
    operator = relationship("User")
