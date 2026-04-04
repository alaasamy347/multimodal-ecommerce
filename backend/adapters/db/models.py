from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class DBProduct(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    image_url = Column(String)

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    session_id = Column(String) # For simple session-based carts

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    total_amount = Column(Float)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

def get_engine(db_url="sqlite:///./multiview_ecommerce.db"):
    return create_engine(db_url, connect_args={"check_same_thread": False})

def init_db(engine):
    Base.metadata.create_all(bind=engine)
