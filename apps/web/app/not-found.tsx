import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-900 text-gray-100">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-indigo-400">404</h1>
        <p className="mt-4 text-xl">Page Not Found</p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-lg bg-indigo-600 px-6 py-3 text-white hover:bg-indigo-500"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
