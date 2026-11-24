"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Dialog, DialogPanel } from "@headlessui/react";
import {
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  MagnifyingGlassIcon,
  BookmarkIcon,
  CalendarIcon,
  Cog6ToothIcon,
} from "@heroicons/react/24/outline";

import { HealthStatus } from "./HealthStatus";

const navigation = [
  { name: "Dashboard", href: "/", icon: HomeIcon },
  { name: "Discover", href: "/discover", icon: MagnifyingGlassIcon },
  { name: "Saved", href: "/saved", icon: BookmarkIcon },
  { name: "Deadlines", href: "/deadlines", icon: CalendarIcon },
  { name: "Settings", href: "/settings", icon: Cog6ToothIcon },
];

export default function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  function renderNavigation() {
    return (
      <nav className="space-y-2">
        {navigation.map((item) => {
          const active = pathname === item.href;

          return (
            <Link
              key={item.name}
              href={item.href}
              aria-current={active ? "page" : undefined}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 rounded-lg px-3 py-3 transition-colors ${
                active
                  ? "bg-indigo-600 text-white"
                  : "text-gray-300 hover:bg-gray-700"
              }`}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <>
      <button
        className="fixed left-4 top-4 z-30 rounded-lg bg-gray-800 p-2 md:hidden"
        onClick={() => setMobileOpen(true)}
        aria-label="Open sidebar"
      >
        <Bars3Icon className="h-6 w-6" />
      </button>

      <aside className="hidden w-64 shrink-0 flex-col border-r border-gray-700 bg-gray-800 p-4 md:flex">
        <div className="mb-10 px-3 pt-4">
          <h1 className="text-2xl font-bold text-indigo-400">
            HackRadar AI
          </h1>
          <p className="mt-2 text-xs text-gray-400">
            Intelligent Event Discovery
          </p>
        </div>

        {renderNavigation()}

        <div className="mt-auto pt-6">
          <HealthStatus />
        </div>
      </aside>

      <Dialog
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        className="relative z-50 md:hidden"
      >
        <div className="fixed inset-0 bg-black/60" aria-hidden="true" />

        <DialogPanel className="fixed inset-y-0 left-0 flex w-64 flex-col bg-gray-800 p-4">
          <button
            className="mb-4 self-end p-2"
            onClick={() => setMobileOpen(false)}
            aria-label="Close sidebar"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>

          <h1 className="mb-6 text-xl font-bold text-indigo-400">
            HackRadar AI
          </h1>

          {renderNavigation()}

          <div className="mt-auto pt-6">
            <HealthStatus />
          </div>
        </DialogPanel>
      </Dialog>
    </>
  );
}