from sqlalchemy.orm import Session
from adapters.db.models import DBProduct, CartItem, Order
from domain.entities import Product
from typing import List

class CheckoutService:
    def __init__(self, db_session_factory):
        self.session_factory = db_session_factory
        
    def add_to_cart(self, product_id: int, session_id: str):
        with self.session_factory() as session:
            item = CartItem(product_id=product_id, session_id=session_id)
            session.add(item)
            session.commit()
            return True

    def get_cart_items(self, session_id: str) -> List[int]:
        with self.session_factory() as session:
            items = session.query(CartItem).filter(CartItem.session_id == session_id).all()
            return [item.product_id for item in items]

    def place_order(self, session_id: str):
        with self.session_factory() as session:
            items = session.query(CartItem).filter(CartItem.session_id == session_id).all()
            if not items:
                return None
                
            # Simulate total (just counting items for now)
            total = float(len(items)) * 100.0 
            order = Order(total_amount=total, status="completed")
            session.add(order)
            
            # Clear cart
            session.query(CartItem).filter(CartItem.session_id == session_id).delete()
            session.commit()
            return order.id
