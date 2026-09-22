import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import App from "./App";
const cap = {
  api_version: "v1",
  capability_version: "1",
  canonical_schema_version: "1",
  processor_contract_version: "1",
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
                  ai_mode: "openclip",
                  summary_mode: "rule",
                  chat_mode: "extractive",
                  model_provider: "stub",
                },
      text: async () => "",
    })),
  );
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
});
test("negotiates capabilities and renders empty summary", async () => {
  render(<App />);
  expect(
    await screen.findByText("No precomputed summary for this day."),
  ).toBeInTheDocument();
});
test("search uses stable subject link", async () => {
  render(<App />);
  await screen.findByText("No precomputed summary for this day.");
  fireEvent.click(screen.getByRole("tab", { name: "Search" }));
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
test("status shows v1 provider independently of legacy ai_mode", async () => {
  render(<App />);
  await screen.findByText("No precomputed summary for this day.");
  fireEvent.click(screen.getByRole("tab", { name: "Status" }));
  expect(await screen.findByText(/provider stub/)).toBeInTheDocument();
  expect(screen.getByText(/legacy ai openclip/)).toBeInTheDocument();
  expect(screen.getByText("model_provider")).toBeInTheDocument();
  expect(screen.getByText("legacy ai_mode")).toBeInTheDocument();
});
test("chat polls queued and running jobs until ready, then renders the answer", async () => {
  let jobPolls = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, init?: RequestInit) => ({
      ok: true,
      json: async () => {
        if (input.includes("capabilities")) return cap;
        if (input.includes("summaries")) return { summary: null };
        if (input === "/api/v1/chat/jobs" && init?.method === "POST") {
          return { id: "job-1", conversation_id: 7, status: "queued" };
        }
        if (input === "/api/v1/chat/jobs/job-1") {
          jobPolls += 1;
          if (jobPolls === 1) {
            return { id: "job-1", conversation_id: 7, status: "running" };
          }
          return {
            id: "job-1",
            conversation_id: 7,
            status: "ready",
            answer: {
              content: "Ready answer",
              degraded: false,
              citations: [],
            },
          };
        }
        throw new Error(`Unexpected fetch: ${input}`);
      },
      text: async () => "",
    })),
  );
  render(<App />);
  await screen.findByText("No precomputed summary for this day.");
  fireEvent.click(screen.getByRole("tab", { name: "Chat" }));
  fireEvent.change(screen.getByLabelText("question"), {
    target: { value: "What happened?" },
  });
  vi.useFakeTimers();
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  await act(async () => {
    await vi.runAllTimersAsync();
  });
  expect(screen.getByText("Ready answer")).toBeInTheDocument();
  expect(jobPolls).toBe(2);
});
test("chat failed jobs remain terminal and are not polled", async () => {
  let jobPolls = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, init?: RequestInit) => ({
      ok: true,
      json: async () => {
        if (input.includes("capabilities")) return cap;
        if (input.includes("summaries")) return { summary: null };
        if (input === "/api/v1/chat/jobs" && init?.method === "POST") {
          return {
            id: "job-failed",
            conversation_id: 8,
            status: "failed",
            error_code: "chat_failed",
          };
        }
        if (input === "/api/v1/chat/jobs/job-failed") {
          jobPolls += 1;
        }
        throw new Error(`Unexpected fetch: ${input}`);
      },
      text: async () => "",
    })),
  );
  render(<App />);
  await screen.findByText("No precomputed summary for this day.");
  fireEvent.click(screen.getByRole("tab", { name: "Chat" }));
  fireEvent.change(screen.getByLabelText("question"), {
    target: { value: "What happened?" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  expect(await screen.findByText("Job failed…")).toBeInTheDocument();
  expect(jobPolls).toBe(0);
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
