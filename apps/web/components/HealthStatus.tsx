"use client";

import { api } from "@/lib/api";
import { useEffect, useState } from "react";

export function HealthStatus() {
  const [status, setStatus] = useState<
    "loading" | "online" | "offline"
  >("loading");

  useEffect(() => {
    let active = true;

    async function checkHealth() {
      try {
        const result = await api.health();

        if (active) {
          setStatus(result.status === "ok" ? "online" : "offline");
        }
      } catch {
        if (active) setStatus("offline");
      }
    }

    checkHealth();

    const timer = setInterval(checkHealth, 30000);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const color =
    status === "online"
      ? "bg-green-500"
      : status === "offline"
      ? "bg-red-500"
      : "bg-yellow-500";

  return (
    <div
      role="status"
      className="flex items-center gap-2 rounded-lg bg-gray-900 p-3 text-sm"
    >
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />

      <span>
        {status === "online"
          ? "Backend online"
          : status === "offline"
          ? "Backend offline"
          : "Checking backend..."}
      </span>
    </div>
  );
}