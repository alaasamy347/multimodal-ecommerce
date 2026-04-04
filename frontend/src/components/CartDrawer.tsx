"use client";

import { useCart } from "@/hooks/useCart";

interface Props {
    open: boolean;
    onClose: () => void;
    onCheckout: () => void;
}

export function CartDrawer({ open, onClose, onCheckout }: Props) {
    const { items, removeItem, updateQty, totalItems, totalPrice, sessionId, clearCart } = useCart();

    const handleCheckoutRequested = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const res = await fetch(`${apiUrl}/checkout/order?session_id=${sessionId}`, {
                method: "POST"
            });
            if (res.ok) {
                const data = await res.json();
                console.log("Order placed:", data.order_id);
                // clearCart(); // Keep local items for now to show on confirmation page if needed, or clear it.
                onCheckout();
            } else {
                alert("Checkout failed. Please try again.");
            }
        } catch (err) {
            console.error("Checkout error:", err);
            alert("Network error during checkout.");
        }
    };

    return(
        <>
            {/* Backdrop */}
            {open && (
                <div className="fixed inset-0 bg-black/40 z-40 backdrop-blur-sm"
                    onClick={onClose} />
            )}

            {/* Drawer */}
            <div className={`fixed top-0 right-0 h-full w-full max-w-md bg-white z-50 shadow-2xl flex flex-col
                       transition-transform duration-300 ${open ? "translate-x-0" : "translate-x-full"}`}>

                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                    <div className="flex items-center gap-2">
                        <span className="text-xl">🛒</span>
                        <h2 className="text-lg font-bold text-gray-900">Your Cart</h2>
                        {totalItems > 0 && (
                            <span className="px-2 py-0.5 bg-violet-100 text-violet-700 text-xs font-bold rounded-full">
                                {totalItems}
                            </span>
                        )}
                    </div>
                    <button onClick={onClose}
                        className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-500 text-xl">
                        ×
                    </button>
                </div>

                {/* Items */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                    {items.length === 0 ? (
                        <div className="text-center py-16 text-gray-400">
                            <div className="text-5xl mb-4">🛒</div>
                            <p className="font-medium text-gray-500">Your cart is empty</p>
                            <p className="text-sm mt-1">Search for furniture and add items</p>
                        </div>
                    ) : (
                        items.map(item => (
                            <div key={item.id} className="flex gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                                {/* Image */}
                                <img src={item.image_url} alt={item.name}
                                    className="w-20 h-20 object-cover rounded-lg flex-shrink-0 bg-gray-200"
                                    onError={e => { (e.target as HTMLImageElement).src = "/placeholder.jpg"; }} />

                                {/* Details */}
                                <div className="flex-1 min-w-0">
                                    <p className="font-semibold text-gray-900 text-sm truncate">{item.name}</p>
                                    <p className="text-xs text-gray-400 mt-0.5 capitalize">{item.color} · {item.category}</p>
                                    <p className="text-violet-700 font-bold text-sm mt-1">${item.price}</p>

                                    {/* Qty controls */}
                                    <div className="flex items-center gap-2 mt-2">
                                        <button onClick={() => updateQty(item.id, item.quantity - 1)}
                                            className="w-6 h-6 rounded-full bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-bold flex items-center justify-center">
                                            −
                                        </button>
                                        <span className="text-sm font-medium w-4 text-center">{item.quantity}</span>
                                        <button onClick={() => updateQty(item.id, item.quantity + 1)}
                                            className="w-6 h-6 rounded-full bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-bold flex items-center justify-center">
                                            +
                                        </button>
                                        <button onClick={() => removeItem(item.id)}
                                            className="ml-auto text-red-400 hover:text-red-600 text-xs">
                                            Remove
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Footer */}
                {items.length > 0 && (
                    <div className="border-t border-gray-100 px-6 py-5 space-y-4 bg-white">
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between text-gray-500">
                                <span>Subtotal ({totalItems} items)</span>
                                <span>${totalPrice.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between text-gray-500">
                                <span>Shipping</span>
                                <span className="text-green-600 font-medium">Free</span>
                            </div>
                            <div className="flex justify-between text-gray-900 font-bold text-base pt-2 border-t">
                                <span>Total</span>
                                <span>${totalPrice.toFixed(2)}</span>
                            </div>
                        </div>

                        <button onClick={handleCheckoutRequested}
                            className="w-full py-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl font-semibold hover:from-violet-700 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg active:scale-95">
                            Proceed to Checkout →
                        </button>
                    </div>
                )}
            </div>
        </>
    );
}