import { lazy } from "react";
import type { RouteObject } from "react-router-dom";

const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const BenchmarksPage = lazy(() => import("@/pages/BenchmarksPage"));
const RunsPage = lazy(() => import("@/pages/RunsPage"));
const RunDetailsPage = lazy(() => import("@/pages/RunDetailsPage"));
const TraceViewerPage = lazy(() => import("@/pages/TraceViewerPage"));
const EvaluationReportPage = lazy(() => import("@/pages/EvaluationReportPage"));
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage"));
const ComparePage = lazy(() => import("@/pages/ComparePage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

/** Single source of truth for page routes; consumed by App (rendering) and MainLayout (title lookup via matchRoutes). */
export const pageRoutes: RouteObject[] = [
  { path: "/", element: <DashboardPage />, handle: { title: "Dashboard" } },
  { path: "/benchmarks", element: <BenchmarksPage />, handle: { title: "Benchmarks" } },
  { path: "/runs", element: <RunsPage />, handle: { title: "Run History" } },
  { path: "/runs/:id", element: <RunDetailsPage />, handle: { title: "Run Details" } },
  { path: "/runs/:id/trace", element: <TraceViewerPage />, handle: { title: "Execution Trace" } },
  {
    path: "/runs/:id/evaluation",
    element: <EvaluationReportPage />,
    handle: { title: "Evaluation Report" },
  },
  { path: "/analytics", element: <AnalyticsPage />, handle: { title: "Analytics" } },
  { path: "/compare", element: <ComparePage />, handle: { title: "Compare Runs" } },
  { path: "*", element: <NotFoundPage />, handle: { title: "Not Found" } },
];
