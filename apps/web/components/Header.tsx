"use client";
import Link from 'next/link';

export default function Header() {
  return (
    <header className="border-b border-gray-700 bg-gray-800 p-4 text-gray-200">
      <nav className="container mx-auto flex items-center justify-between">
        <Link href="/">
          <a className="text-xl font-semibold">HackRadar AI</a>
        </Link>
        {/* Future navigation items could go here */}
      </nav>
    </header>
  );
}
