import { Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import { MainLayout } from "@/layouts/MainLayout";
import { pageRoutes } from "@/routes";

function PageFallback() {
  return <div className="p-6 text-sm text-gray-500">Loading…</div>;
}

/** Routes mirror PROJECT_SPEC_4 SS8, with lazy-loaded pages for code splitting (SS28). */
export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route element={<MainLayout />}>
          {pageRoutes.map(({ path, element, handle }) => (
            <Route key={path} path={path} element={element} handle={handle} />
          ))}
        </Route>
      </Routes>
    </Suspense>
  );
}
