"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-900 text-gray-100">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-bold text-red-400">
          Something went wrong
        </h1>
        <p className="mt-4 text-gray-400">
          An unexpected error occurred. Please try again.
        </p>
        <button
          onClick={() => reset()}
          className="mt-6 rounded-lg bg-indigo-600 px-6 py-3 text-white hover:bg-indigo-500"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}
