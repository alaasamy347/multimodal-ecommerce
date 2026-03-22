"use client";

import { useCart } from "@/hooks/useCart";
import { useState } from "react";

interface Props {
    onBack: () => void;
    onSuccess: (orderId: string) => void;
}

type Step = "shipping" | "payment" | "review";

interface ShippingForm {
    firstName: string; lastName: string; email: string;
    phone: string; address: string; city: string;
    country: string; zip: string;
}

interface PaymentForm {
    cardName: string; cardNumber: string;
    expiry: string; cvv: string;
}

const EMPTY_SHIPPING: ShippingForm = {
    firstName: "", lastName: "", email: "", phone: "",
    address: "", city: "", country: "Egypt", zip: "",
};

const EMPTY_PAYMENT: PaymentForm = {
    cardName: "", cardNumber: "", expiry: "", cvv: "",
};

function StepIndicator({ current }: { current: Step }) {
    const steps: { key: Step; label: string; icon: string }[] = [
        { key: "shipping", label: "Shipping", icon: "📦" },
        { key: "payment", label: "Payment", icon: "💳" },
        { key: "review", label: "Review", icon: "✅" },
    ];
    const idx = steps.findIndex(s => s.key === current);
    return (
        <div className="flex items-center justify-center gap-0 mb-8">
            {steps.map((step, i) => (
                <div key={step.key} className="flex items-center">
                    <div className={`flex flex-col items-center gap-1`}>
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold border-2 transition-all
              ${i <= idx ? "bg-violet-600 border-violet-600 text-white" : "bg-white border-gray-200 text-gray-400"}`}>
                            {i < idx ? "✓" : step.icon}
                        </div>
                        <span className={`text-xs font-medium ${i <= idx ? "text-violet-700" : "text-gray-400"}`}>
                            {step.label}
                        </span>
                    </div>
                    {i < steps.length - 1 && (
                        <div className={`w-16 h-0.5 mx-2 mb-4 ${i < idx ? "bg-violet-400" : "bg-gray-200"}`} />
                    )}
                </div>
            ))}
        </div>
    );
}

function Field({ label, value, onChange, placeholder, type = "text", half = false }: any) {
    return (
        <div className={half ? "col-span-1" : "col-span-2"}>
            <label className="block text-xs font-semibold text-gray-600 mb-1">{label}</label>
            <input
                type={type}
                value={value}
                onChange={e => onChange(e.target.value)}
                placeholder={placeholder}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100 transition-all"
            />
        </div>
    );
}

export function CheckoutPage({ onBack, onSuccess }: Props) {
    const { items, totalPrice, totalItems } = useCart();
    const [step, setStep] = useState<Step>("shipping");
    const [shipping, setShipping] = useState<ShippingForm>(EMPTY_SHIPPING);
    const [payment, setPayment] = useState<PaymentForm>(EMPTY_PAYMENT);
    const [placing, setPlacing] = useState(false);

    const sh = (k: keyof ShippingForm) => (v: string) => setShipping(p => ({ ...p, [k]: v }));
    const pm = (k: keyof PaymentForm) => (v: string) => setPayment(p => ({ ...p, [k]: v }));

    // Format card number with spaces
    const formatCard = (v: string) =>
        v.replace(/\D/g, "").slice(0, 16).replace(/(.{4})/g, "$1 ").trim();

    // Format expiry MM/YY
    const formatExpiry = (v: string) => {
        const d = v.replace(/\D/g, "").slice(0, 4);
        return d.length > 2 ? d.slice(0, 2) + "/" + d.slice(2) : d;
    };

    async function placeOrder() {
        setPlacing(true);
        // Simulate network delay
        await new Promise(r => setTimeout(r, 1800));
        const orderId = "ORD-" + Math.random().toString(36).slice(2, 8).toUpperCase();
        onSuccess(orderId);
    }

    const shippingValid = Object.values(shipping).every(v => v.trim() !== "");
    const paymentValid = payment.cardName && payment.cardNumber.replace(/\s/g, "").length === 16
        && payment.expiry.length === 5 && payment.cvv.length >= 3;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-violet-50/20 to-indigo-50/40">
            <div className="max-w-5xl mx-auto px-4 py-10">

                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button onClick={onBack}
                        className="flex items-center gap-2 text-sm text-gray-500 hover:text-violet-700 transition-colors">
                        ← Back to results
                    </button>
                    <div className="flex-1" />
                    <div className="text-sm text-gray-400">{totalItems} item{totalItems !== 1 ? "s" : ""} · <strong className="text-gray-800">${totalPrice.toFixed(2)}</strong></div>
                </div>

                <StepIndicator current={step} />

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Form area */}
                    <div className="lg:col-span-2">

                        {/* ── SHIPPING ── */}
                        {step === "shipping" && (
                            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                                <h2 className="text-lg font-bold text-gray-900 mb-5">📦 Shipping Information</h2>
                                <div className="grid grid-cols-2 gap-4">
                                    <Field label="First Name" value={shipping.firstName} onChange={sh("firstName")} placeholder="Alaa" half />
                                    <Field label="Last Name" value={shipping.lastName} onChange={sh("lastName")} placeholder="Samy" half />
                                    <Field label="Email" value={shipping.email} onChange={sh("email")} placeholder="you@email.com" type="email" />
                                    <Field label="Phone" value={shipping.phone} onChange={sh("phone")} placeholder="+20 100 000 0000" />
                                    <Field label="Address" value={shipping.address} onChange={sh("address")} placeholder="123 Nile St, Apt 4" />
                                    <Field label="City" value={shipping.city} onChange={sh("city")} placeholder="Alexandria" half />
                                    <Field label="ZIP / Postal" value={shipping.zip} onChange={sh("zip")} placeholder="21500" half />
                                    <Field label="Country" value={shipping.country} onChange={sh("country")} placeholder="Egypt" />
                                </div>
                                <button onClick={() => setStep("payment")} disabled={!shippingValid}
                                    className="mt-6 w-full py-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl font-semibold disabled:opacity-40 hover:from-violet-700 hover:to-indigo-700 transition-all">
                                    Continue to Payment →
                                </button>
                            </div>
                        )}

                        {/* ── PAYMENT ── */}
                        {step === "payment" && (
                            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                                <h2 className="text-lg font-bold text-gray-900 mb-1">💳 Payment Details</h2>
                                <p className="text-xs text-gray-400 mb-5">This is a demo — no real payment is processed.</p>

                                {/* Card preview */}
                                <div className="bg-gradient-to-br from-violet-600 to-indigo-700 rounded-2xl p-5 mb-6 text-white shadow-lg">
                                    <div className="flex justify-between items-start mb-6">
                                        <div className="text-xs opacity-70 font-medium tracking-widest uppercase">Multiview Pay</div>
                                        <div className="text-2xl">💳</div>
                                    </div>
                                    <div className="text-xl font-mono tracking-widest mb-4">
                                        {payment.cardNumber || "•••• •••• •••• ••••"}
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <div>
                                            <div className="opacity-60 text-xs">Card Holder</div>
                                            <div className="font-medium">{payment.cardName || "YOUR NAME"}</div>
                                        </div>
                                        <div>
                                            <div className="opacity-60 text-xs">Expires</div>
                                            <div className="font-medium">{payment.expiry || "MM/YY"}</div>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <Field label="Cardholder Name" value={payment.cardName}
                                        onChange={pm("cardName")} placeholder="Alaa Samy" />
                                    <div className="col-span-2">
                                        <label className="block text-xs font-semibold text-gray-600 mb-1">Card Number</label>
                                        <input type="text" value={payment.cardNumber}
                                            onChange={e => setPayment(p => ({ ...p, cardNumber: formatCard(e.target.value) }))}
                                            placeholder="1234 5678 9012 3456"
                                            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-sm font-mono focus:outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100" />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-semibold text-gray-600 mb-1">Expiry</label>
                                        <input type="text" value={payment.expiry}
                                            onChange={e => setPayment(p => ({ ...p, expiry: formatExpiry(e.target.value) }))}
                                            placeholder="MM/YY"
                                            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100" />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-semibold text-gray-600 mb-1">CVV</label>
                                        <input type="password" value={payment.cvv} maxLength={4}
                                            onChange={e => setPayment(p => ({ ...p, cvv: e.target.value.replace(/\D/g, "") }))}
                                            placeholder="•••"
                                            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100" />
                                    </div>
                                </div>

                                <div className="flex gap-3 mt-6">
                                    <button onClick={() => setStep("shipping")}
                                        className="flex-1 py-3 border border-gray-200 rounded-xl text-gray-600 font-medium hover:bg-gray-50 transition-all">
                                        ← Back
                                    </button>
                                    <button onClick={() => setStep("review")} disabled={!paymentValid}
                                        className="flex-1 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl font-semibold disabled:opacity-40 hover:from-violet-700 hover:to-indigo-700 transition-all">
                                        Review Order →
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* ── REVIEW ── */}
                        {step === "review" && (
                            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">
                                <h2 className="text-lg font-bold text-gray-900">✅ Review Your Order</h2>

                                {/* Shipping summary */}
                                <div className="bg-gray-50 rounded-xl p-4 text-sm">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-semibold text-gray-700">📦 Shipping to</span>
                                        <button onClick={() => setStep("shipping")} className="text-violet-600 text-xs hover:underline">Edit</button>
                                    </div>
                                    <p className="text-gray-600">{shipping.firstName} {shipping.lastName}</p>
                                    <p className="text-gray-500 text-xs">{shipping.address}, {shipping.city}, {shipping.country} {shipping.zip}</p>
                                    <p className="text-gray-500 text-xs">{shipping.email} · {shipping.phone}</p>
                                </div>

                                {/* Payment summary */}
                                <div className="bg-gray-50 rounded-xl p-4 text-sm">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-semibold text-gray-700">💳 Payment</span>
                                        <button onClick={() => setStep("payment")} className="text-violet-600 text-xs hover:underline">Edit</button>
                                    </div>
                                    <p className="text-gray-600">{payment.cardName}</p>
                                    <p className="text-gray-500 text-xs">•••• •••• •••• {payment.cardNumber.slice(-4)}</p>
                                </div>

                                {/* Items */}
                                <div className="space-y-3">
                                    {items.map(item => (
                                        <div key={item.id} className="flex gap-3 items-center">
                                            <img src={item.image_url} alt={item.name}
                                                className="w-14 h-14 object-cover rounded-lg bg-gray-100"
                                                onError={e => { (e.target as HTMLImageElement).src = "/placeholder.jpg"; }} />
                                            <div className="flex-1">
                                                <p className="text-sm font-medium text-gray-800 truncate">{item.name}</p>
                                                <p className="text-xs text-gray-400 capitalize">{item.color} · qty {item.quantity}</p>
                                            </div>
                                            <p className="text-sm font-bold text-gray-800">${(item.price * item.quantity).toFixed(2)}</p>
                                        </div>
                                    ))}
                                </div>

                                <div className="flex gap-3 pt-2">
                                    <button onClick={() => setStep("payment")}
                                        className="flex-1 py-3 border border-gray-200 rounded-xl text-gray-600 font-medium hover:bg-gray-50 transition-all">
                                        ← Back
                                    </button>
                                    <button onClick={placeOrder} disabled={placing}
                                        className="flex-1 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-bold hover:from-green-600 hover:to-emerald-700 transition-all shadow-md disabled:opacity-60">
                                        {placing ? (
                                            <span className="flex items-center justify-center gap-2">
                                                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                                Placing Order...
                                            </span>
                                        ) : "Place Order 🎉"}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Order summary sidebar */}
                    <div className="lg:col-span-1">
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 sticky top-6">
                            <h3 className="font-bold text-gray-900 mb-4">Order Summary</h3>
                            <div className="space-y-3 max-h-64 overflow-y-auto">
                                {items.map(item => (
                                    <div key={item.id} className="flex gap-2 items-center">
                                        <img src={item.image_url} alt={item.name}
                                            className="w-12 h-12 object-cover rounded-lg bg-gray-100 flex-shrink-0"
                                            onError={e => { (e.target as HTMLImageElement).src = "/placeholder.jpg"; }} />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-medium text-gray-700 truncate">{item.name}</p>
                                            <p className="text-xs text-gray-400">×{item.quantity}</p>
                                        </div>
                                        <p className="text-xs font-bold">${(item.price * item.quantity).toFixed(2)}</p>
                                    </div>
                                ))}
                            </div>
                            <div className="border-t border-gray-100 mt-4 pt-4 space-y-2 text-sm">
                                <div className="flex justify-between text-gray-500">
                                    <span>Subtotal</span><span>${totalPrice.toFixed(2)}</span>
                                </div>
                                <div className="flex justify-between text-gray-500">
                                    <span>Shipping</span><span className="text-green-600 font-medium">Free</span>
                                </div>
                                <div className="flex justify-between text-gray-900 font-bold text-base border-t pt-2">
                                    <span>Total</span><span>${totalPrice.toFixed(2)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}