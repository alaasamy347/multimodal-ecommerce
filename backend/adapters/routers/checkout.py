from fastapi import APIRouter, Depends, HTTPException
from use_cases.checkout_service import CheckoutService
from typing import List

router = APIRouter(prefix="/checkout")

def get_checkout_service() -> CheckoutService:
    raise NotImplementedError

@router.post("/cart/add/{product_id}")
async def add_to_cart(product_id: int, session_id: str = "default", service: CheckoutService = Depends(get_checkout_service)):
    service.add_to_cart(product_id, session_id)
    return {"status": "success", "message": f"Product {product_id} added to cart"}

@router.get("/cart")
async def get_cart(session_id: str = "default", service: CheckoutService = Depends(get_checkout_service)):
    items = service.get_cart_items(session_id)
    return {"session_id": session_id, "items": items}

@router.post("/order")
async def place_order(session_id: str = "default", service: CheckoutService = Depends(get_checkout_service)):
    order_id = service.place_order(session_id)
    if not order_id:
        raise HTTPException(status_code=400, detail="Cart is empty")
    return {"status": "success", "order_id": order_id}
