import { AlertOctagon } from "lucide-react";
import React from "react";

import { Button } from "@/components/ui/Button";

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Catches any render-time exception in the page it wraps and shows a clear message instead of
 * letting React silently unmount the whole tree (React's default for an uncaught error during
 * render is a blank page, with the actual error visible only in the browser console -- easy to
 * miss, and indistinguishable from "nothing rendered" or "still loading" to anyone who isn't
 * looking). No page in this app had any error boundary before this one; MainLayout wraps every
 * route with it, keyed by pathname so navigating to a different page always gets a fresh boundary
 * rather than staying stuck on a previous page's error.
 *
 * Must be a class component -- React has no hook-based equivalent to
 * ``static getDerivedStateFromError`` / ``componentDidCatch``.
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error("Unhandled error rendering this page:", error, info.componentStack);
  }

  render(): React.ReactNode {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center rounded-lg border border-danger-100 bg-danger-100/40 px-6 py-12 text-center dark:border-danger-600/30 dark:bg-danger-600/10">
          <AlertOctagon className="mb-3 h-8 w-8 text-danger-600" aria-hidden="true" />
          <p className="font-medium text-danger-700 dark:text-danger-600">
            Something went wrong displaying this page.
          </p>
          <p className="mt-1 max-w-sm text-sm text-danger-600/80">
            {this.state.error.message || "An unexpected error occurred."}
          </p>
          <Button
            variant="secondary"
            size="sm"
            className="mt-4"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
