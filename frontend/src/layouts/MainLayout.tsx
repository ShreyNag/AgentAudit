import { Outlet, matchRoutes, useLocation } from "react-router-dom";

import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { SidebarProvider } from "@/context/SidebarContext";
import { pageRoutes } from "@/routes";

/** The primary application shell: sidebar + header + page content (PROJECT_SPEC_4 SS9/SS134). */
export function MainLayout() {
  const location = useLocation();
  const matches = matchRoutes(pageRoutes, location);
  const current = matches?.at(-1);
  const title = (current?.route.handle as { title?: string } | undefined)?.title ?? "AgentAudit";

  return (
    <SidebarProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header title={title} />
          <main className="flex-1 overflow-y-auto bg-gray-50 p-6 dark:bg-gray-950">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
