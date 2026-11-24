"use client";
import Link from 'next/link';

export default function Discover() {
  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-bold">Discover Hackathons</h1>
      <input
        type="text"
        placeholder="Search events…"
        className="w-full rounded border border-gray-700 bg-gray-800 p-2 text-gray-100 disabled:opacity-50"
        disabled
      />
      <p className="text-gray-500">No events loaded yet. The discovery feature will be added later.</p>
    </section>
  );
}
