import React, { useEffect, useMemo, useState } from "react";

import { ThemeContext, type Theme } from "@/context/theme-context";

const STORAGE_KEY = "agentaudit-theme";

function resolveSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/** Persists the theme preference locally (PROJECT_SPEC_4 SS25). No execution data lives here. */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return (stored as Theme) ?? "system";
  });
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">(() =>
    theme === "system" ? resolveSystemTheme() : theme,
  );

  useEffect(() => {
    const next = theme === "system" ? resolveSystemTheme() : theme;
    setResolvedTheme(next);
    document.documentElement.classList.toggle("dark", next === "dark");
  }, [theme]);

  useEffect(() => {
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const listener = () => {
      const next = resolveSystemTheme();
      setResolvedTheme(next);
      document.documentElement.classList.toggle("dark", next === "dark");
    };
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, [theme]);

  const setTheme = (next: Theme) => {
    localStorage.setItem(STORAGE_KEY, next);
    setThemeState(next);
  };

  const value = useMemo(() => ({ theme, resolvedTheme, setTheme }), [theme, resolvedTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
