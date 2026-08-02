import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Badge } from "@/components/ui/Badge";
import { behaviourTone, statusTone, trustLevelTone } from "@/components/ui/badgeTones";

describe("Badge", () => {
  it("renders its children", () => {
    render(<Badge tone="success">Completed</Badge>);
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });
});

describe("statusTone", () => {
  it("maps known statuses to the expected tone", () => {
    expect(statusTone("completed")).toBe("success");
    expect(statusTone("failed")).toBe("danger");
    expect(statusTone("running")).toBe("info");
    expect(statusTone("queued")).toBe("neutral");
  });

  it("falls back to neutral for unknown statuses", () => {
    expect(statusTone("something-else")).toBe("neutral");
  });
});

describe("behaviourTone", () => {
  it("marks UNSAFE_COMPLIANCE as danger", () => {
    expect(behaviourTone("UNSAFE_COMPLIANCE")).toBe("danger");
  });

  it("marks SAFE_CORRECT as success", () => {
    expect(behaviourTone("SAFE_CORRECT")).toBe("success");
  });
});

describe("trustLevelTone", () => {
  it("marks High Trust and above as success", () => {
    expect(trustLevelTone("Very High Trust")).toBe("success");
    expect(trustLevelTone("High Trust")).toBe("success");
  });

  it("marks Moderate/Limited Trust as warning", () => {
    expect(trustLevelTone("Moderate Trust")).toBe("warning");
    expect(trustLevelTone("Limited Trust")).toBe("warning");
  });

  it("marks everything else as danger", () => {
    expect(trustLevelTone("Untrusted")).toBe("danger");
    expect(trustLevelTone("Low Trust")).toBe("danger");
  });
});
