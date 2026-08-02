import { Link } from "react-router-dom";

import { Button } from "@/components/ui/Button";

/** Standardized 404 view (PROJECT_SPEC_4 SS142). */
export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <p className="text-5xl font-bold text-gray-300 dark:text-gray-700">404</p>
      <p className="mt-2 text-lg font-medium">Page not found</p>
      <p className="mt-1 text-sm text-gray-500">The page you're looking for doesn't exist.</p>
      <Link to="/" className="mt-6">
        <Button>Return to Dashboard</Button>
      </Link>
    </div>
  );
}
