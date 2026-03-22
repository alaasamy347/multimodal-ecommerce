"use client";

import { useCart } from "@/hooks/useCart";
import { useEffect, useState } from "react";

interface Props {
    orderId: string;
    onContinue: () => void;
}

export function OrderConfirmation({ orderId, onContinue }: Props) {
    const { items, totalPrice, clearCart } = useCart();
    const [cleared, setCleared] = useState(false);

    // Save snapshot before clearing
    const [snapshot] = useState({ items: [...items], total: totalPrice });

    useEffect(() => {
        if (!cleared) { clearCart(); setCleared(true); }
    }, [cleared, clearCart]);

    const eta = new Date();
    eta.setDate(eta.getDate() + 5);
    const etaStr = eta.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

    return (
        <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50/30 to-teal-50 flex items-center justify-center px-4 py-12">
            <div className="max-w-lg w-full">

                {/* Success animation */}
                <div className="text-center mb-8">
                    <div className="w-24 h-24 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl"
                        style={{ animation: "popIn 0.5s cubic-bezier(0.175,0.885,0.32,1.275)" }}>
                        <span className="text-4xl">✓</span>
                    </div>
                    <style>{`@keyframes popIn{0%{transform:scale(0)}100%{transform:scale(1)}}`}</style>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Order Confirmed! 🎉</h1>
                    <p className="text-gray-500">Thank you for your purchase. Your furniture is on its way.</p>
                </div>

                {/* Order card */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-6">

                    {/* Order ID banner */}
                    <div className="bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-4 text-white">
                        <div className="flex justify-between items-center">
                            <div>
                                <p className="text-xs opacity-70 font-medium">Order ID</p>
                                <p className="font-bold text-lg tracking-wider">{orderId}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-xs opacity-70">Estimated Delivery</p>
                                <p className="font-semibold text-sm">{etaStr}</p>
                            </div>
                        </div>
                    </div>

                    {/* Items */}
                    <div className="p-5 space-y-3">
                        {snapshot.items.map(item => (
                            <div key={item.id} className="flex gap-3 items-center">
                                <img src={item.image_url} alt={item.name}
                                    className="w-14 h-14 object-cover rounded-xl bg-gray-100 flex-shrink-0"
                                    onError={e => { (e.target as HTMLImageElement).src = "/placeholder.jpg"; }} />
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-gray-800 truncate">{item.name}</p>
                                    <p className="text-xs text-gray-400 capitalize">{item.color} · Qty {item.quantity}</p>
                                </div>
                                <p className="text-sm font-bold text-gray-700">${(item.price * item.quantity).toFixed(2)}</p>
                            </div>
                        ))}
                    </div>

                    {/* Total */}
                    <div className="border-t border-gray-100 px-5 py-4 flex justify-between items-center bg-gray-50">
                        <span className="font-semibold text-gray-700">Total Paid</span>
                        <span className="text-xl font-bold text-gray-900">${snapshot.total.toFixed(2)}</span>
                    </div>
                </div>

                {/* Timeline */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-6">
                    <h3 className="font-semibold text-gray-800 mb-4 text-sm">Order Progress</h3>
                    <div className="space-y-3">
                        {[
                            { label: "Order Placed", done: true, icon: "✅" },
                            { label: "Payment Confirmed", done: true, icon: "💳" },
                            { label: "Being Prepared", done: false, icon: "📦" },
                            { label: "Shipped", done: false, icon: "🚚" },
                            { label: "Delivered", done: false, icon: "🏠" },
                        ].map((step, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <span className="text-lg">{step.icon}</span>
                                <div className="flex-1 h-0.5 bg-gray-100 relative">
                                    <div className={`h-full transition-all ${step.done ? "bg-green-400" : "bg-gray-200"}`} style={{ width: step.done ? "100%" : "0%" }} />
                                </div>
                                <span className={`text-xs font-medium ${step.done ? "text-green-600" : "text-gray-400"}`}>
                                    {step.label}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* CTA */}
                <button onClick={onContinue}
                    className="w-full py-4 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-2xl font-bold text-base hover:from-violet-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl active:scale-95">
                    Continue Shopping
                </button>
            </div>
        </div>
    );
}