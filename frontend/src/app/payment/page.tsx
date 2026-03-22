"use client";

import { useRouter } from "next/navigation";

export default function PaymentPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center">
      <h1 className="text-3xl font-bold mb-4">Payment</h1>

      <button
        onClick={() => router.push("/success")}
        className="mt-6 px-6 py-3 bg-green-600 text-white rounded-lg"
      >
        Pay Now
      </button>
    </div>
  );
}