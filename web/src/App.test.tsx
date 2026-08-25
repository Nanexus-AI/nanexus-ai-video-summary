import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import App from "./App";
const cap = {
  api_version: "v1",
  subject_reference: "uuid",
  subject_path_template: "/api/v1/subjects/{subject_id}",
  summary: { available: true, asynchronous: true },
  search: { available: true, asynchronous: false },
  chat: { available: true, asynchronous: true },
  legacy_fallback_available: true,
  ownership_authentication: "not-configured",
};
beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => ({
      ok: true,
      json: async () =>
        input.includes("capabilities")
          ? cap
          : input.includes("summaries")
            ? { summary: null }
            : input.includes("search")
              ? {
                  items: [
                    {
                      subject_id: "58e8dd46-66d0-4ac4-a025-7a44af2b6722",
                      score: 0.9,
                      labels: ["person"],
                      subject_path:
                        "/api/v1/subjects/58e8dd46-66d0-4ac4-a025-7a44af2b6722",
                    },
                  ],
                  degraded: false,
                }
              : {
                  status: "ok",
                  database: true,
                  redis: true,
                  ai_mode: "stub",
                  summary_mode: "rule",
                  chat_mode: "extractive",
                },
      text: async () => "",
    })),
  );
});
afterEach(cleanup);
test("negotiates capabilities and renders empty summary", async () => {
  render(<App />);
  expect(
    await screen.findByText("No precomputed summary for this day."),
  ).toBeInTheDocument();
});
test("search uses stable subject link", async () => {
  render(<App />);
  await screen.findByText("No precomputed summary for this day.");
  fireEvent.click(screen.getByText("search"));
  fireEvent.change(screen.getByLabelText("query"), {
    target: { value: "person" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Search" }));
  const link = await screen.findByText(/Related event/);
  expect(link).toHaveAttribute(
    "href",
    "/api/v1/subjects/58e8dd46-66d0-4ac4-a025-7a44af2b6722",
  );
});
test("shows retryable capability error", async () => {
  (fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
    new Error("offline"),
  );
  render(<App />);
  expect(
    await screen.findByText(/Capability incompatible/),
  ).toBeInTheDocument();
  expect(screen.getByText("Retry")).toBeInTheDocument();
});
