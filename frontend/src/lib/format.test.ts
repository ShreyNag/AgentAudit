import { describe, expect, it } from "vitest";

import { formatDateTime, formatDuration, formatPercent, formatScore, titleCase } from "@/lib/format";

describe("formatDuration", () => {
  it("formats sub-second durations in milliseconds", () => {
    expect(formatDuration(0.25)).toBe("250ms");
  });

  it("formats sub-minute durations in seconds", () => {
    expect(formatDuration(12.34)).toBe("12.3s");
  });

  it("formats durations over a minute as minutes and seconds", () => {
    expect(formatDuration(125)).toBe("2m 5s");
  });

  it("returns an em dash for null/undefined", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(undefined)).toBe("—");
  });
});

describe("formatScore", () => {
  it("formats to one decimal place by default", () => {
    expect(formatScore(8.456)).toBe("8.5");
  });

  it("supports a custom digit count", () => {
    expect(formatScore(8.456, 2)).toBe("8.46");
  });

  it("returns an em dash for missing values", () => {
    expect(formatScore(null)).toBe("—");
  });
});

describe("formatPercent", () => {
  it("converts a 0-1 fraction into a rounded percentage", () => {
    expect(formatPercent(0.873)).toBe("87%");
  });

  it("returns an em dash for missing values", () => {
    expect(formatPercent(undefined)).toBe("—");
  });
});

describe("formatDateTime", () => {
  it("returns an em dash for missing values", () => {
    expect(formatDateTime(null)).toBe("—");
  });

  it("formats a valid ISO string as a locale string", () => {
    const result = formatDateTime("2026-01-01T00:00:00Z");
    expect(result).not.toBe("—");
    expect(result.length).toBeGreaterThan(0);
  });
});

describe("titleCase", () => {
  it("converts snake_case to Title Case", () => {
    expect(titleCase("tool_faithfulness")).toBe("Tool Faithfulness");
  });

  it("converts SCREAMING_SNAKE_CASE classifications to Title Case", () => {
    expect(titleCase("SAFE_BY_INCOMPETENCE")).toBe("SAFE BY INCOMPETENCE");
  });
});
