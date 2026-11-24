import "./globals.css";
import type { ReactNode } from "react";
import Sidebar from "../components/Sidebar";

export const metadata = {
  title: "HackRadar AI",
  description: "AI-powered event discovery dashboard",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="flex min-h-screen bg-gray-900 font-sans text-gray-100">
        <Sidebar />

        <main className="min-w-0 flex-1 overflow-y-auto p-6 pt-20 md:pt-6">
          {children}
        </main>
      </body>
    </html>
  );
}