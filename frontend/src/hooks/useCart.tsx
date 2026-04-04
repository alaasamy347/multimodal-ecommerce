"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

export interface CartItem {
  id: number;
  name: string;
  category: string;
  color: string;
  image_url: string;
  score: number;
  quantity: number;
  price: number;
}

interface CartContextType {
  items: CartItem[];
  addItem: (product: Omit<CartItem, "quantity" | "price">) => Promise<void>;
  removeItem: (id: number) => void;
  updateQty: (id: number, qty: number) => void;
  clearCart: () => void;
  totalItems: number;
  totalPrice: number;
  sessionId: string;
}

const CartContext = createContext<CartContextType | null>(null);

// Destructure Provider to avoid Namespace "CartContext" errors
const { Provider } = CartContext;

function priceFromId(id: number) {
  const prices = [149, 199, 249, 299, 349, 399, 449, 499, 549, 599];
  return prices[id % prices.length];
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [sessionId] = useState(() => `session-${Date.now()}`);

  const addItem = useCallback(async (product: Omit<CartItem, "quantity" | "price">) => {
    // 1. Sync with backend
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${apiUrl}/checkout/cart/add/${product.id}?session_id=${sessionId}`, {
        method: "POST"
      });
    } catch (err) {
      console.error("Failed to sync cart item to backend", err);
    }

    // 2. Update local state
    setItems((prev) => {
      const existing = prev.find((i) => i.id === product.id);
      if (existing) {
        return prev.map((i) =>
          i.id === product.id ? { ...i, quantity: i.quantity + 1 } : i
        );
      }
      return [
        ...prev,
        { ...product, quantity: 1, price: priceFromId(product.id) },
      ];
    });
  }, [sessionId]);

  const removeItem = useCallback((id: number) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
  }, []);

  const updateQty = useCallback(
    (id: number, qty: number) => {
      if (qty <= 0) {
        removeItem(id);
        return;
      }
      setItems((prev) =>
        prev.map((i) => (i.id === id ? { ...i, quantity: qty } : i))
      );
    },
    [removeItem]
  );

  const clearCart = useCallback(() => setItems([]), []);

  const totalItems = items.reduce((s, i) => s + i.quantity, 0);
  const totalPrice = items.reduce((s, i) => s + i.price * i.quantity, 0);

  return (
    <Provider
      value={{
        items,
        addItem,
        removeItem,
        updateQty,
        clearCart,
        totalItems,
        totalPrice,
        sessionId
      }}
    >
      {children}
    </Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be inside CartProvider");
  return ctx;
}