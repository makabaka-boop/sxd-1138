from app.database import SessionLocal, engine, Base
from app.models import User, Store, ServiceItem
from app.auth import get_password_hash
from app.enums import UserRole
from app.logger import logger


def init_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            logger.info("数据已初始化，跳过")
            return

        store = Store(
            name="总店",
            address="北京市朝阳区洗护路1号",
            phone="010-12345678",
            manager="张经理",
            default_urgent_fee=10.0,
            default_urgent_description="24小时内取件"
        )
        db.add(store)
        db.flush()

        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="系统管理员",
            role=UserRole.ADMIN,
            phone="13800138000",
            store_id=store.id
        )

        operator = User(
            username="operator",
            hashed_password=get_password_hash("operator123"),
            full_name="李操作员",
            role=UserRole.OPERATOR,
            phone="13800138001",
            store_id=store.id
        )

        inspector = User(
            username="inspector",
            hashed_password=get_password_hash("inspector123"),
            full_name="王审核员",
            role=UserRole.INSPECTOR,
            phone="13800138002",
            store_id=store.id
        )

        db.add_all([admin, operator, inspector])
        db.flush()

        services = [
            ServiceItem(name="普通干洗", description="标准干洗服务", price=35.0, duration_minutes=60, store_id=store.id, urgent_fee=15.0, urgent_description="当日取件"),
            ServiceItem(name="高档西装干洗", description="高档面料专业干洗", price=88.0, duration_minutes=90, store_id=store.id, urgent_fee=30.0, urgent_description="当日取件"),
            ServiceItem(name="水洗", description="普通衣物水洗", price=20.0, duration_minutes=45, store_id=store.id, urgent_fee=10.0, urgent_description="当日取件"),
            ServiceItem(name="羽绒服清洗", description="羽绒服专业清洗", price=68.0, duration_minutes=120, store_id=store.id, urgent_fee=25.0, urgent_description="次日取件"),
            ServiceItem(name="皮衣护理", description="皮衣清洁保养", price=158.0, duration_minutes=180, store_id=store.id, urgent_fee=50.0, urgent_description="次日取件"),
        ]
        db.add_all(services)

        db.commit()
        logger.info("数据初始化完成")
        logger.info("默认账号:")
        logger.info("  管理员: admin / admin123")
        logger.info("  操作员: operator / operator123")
        logger.info("  审核员: inspector / inspector123")

    except Exception as e:
        logger.error(f"数据初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_data()
