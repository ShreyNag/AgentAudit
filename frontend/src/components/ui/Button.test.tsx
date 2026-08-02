import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Button } from "@/components/ui/Button";

describe("Button", () => {
  it("renders children and responds to clicks", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Launch</Button>);
    fireEvent.click(screen.getByRole("button", { name: "Launch" }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("disables the button and shows a busy state while loading", () => {
    render(<Button loading>Submit</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("does not fire onClick while disabled", () => {
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        Submit
      </Button>,
    );
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });
});
