import { FormEvent, ReactNode, useEffect, useState } from "react";
import {
  api,
  Capabilities,
  ChatJob,
  SearchHit,
  SearchResponse,
  Summary,
  SummaryHighlight,
  subjectHref,
} from "./api";
import "./styles.css";

type Page = "summary" | "search" | "chat" | "status" | "settings";

const PAGES: { id: Page; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "search", label: "Search" },
  { id: "chat", label: "Chat" },
  { id: "status", label: "Status" },
  { id: "settings", label: "Settings" },
];

const compatible = (cap: Capabilities) =>
  cap.api_version === "v1" &&
  cap.capability_version === "1" &&
  cap.canonical_schema_version === "1" &&
  cap.processor_contract_version === "1" &&
  cap.subject_reference === "uuid";

const compactTime = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

const State = ({
  loading,
  error,
  empty,
  retry,
}: {
  loading?: boolean;
  error?: string;
  empty?: string;
  retry?: () => void;
}) =>
  loading ? (
    <p className="state-box" role="status">
      Loading…
    </p>
  ) : error ? (
    <div className="state-box" role="alert">
      <p>{error}</p>
      {retry && (
        <button className="btn" type="button" onClick={retry}>
          Retry
        </button>
      )}
    </div>
  ) : empty ? (
    <p className="state-box">{empty}</p>
  ) : null;

const Subject = ({ id }: { id: string }) => (
  <a href={subjectHref(id)} target="_blank" rel="noreferrer">
    Related event {id.slice(0, 8)}
  </a>
);

const Pill = ({
  children,
  tone = "default",
  dot = false,
}: {
  children: ReactNode;
  tone?: "default" | "ok" | "warn" | "bad" | "label";
  dot?: boolean;
}) => (
  <span
    className={`pill${tone !== "default" ? ` pill-${tone}` : ""}${dot ? " pill-dot" : ""}`}
  >
    {children}
  </span>
);

const PageHead = ({ title, children }: { title: string; children: string }) => (
  <div className="page-head">
    <div>
      <h2>{title}</h2>
      <p className="page-sub">{children}</p>
    </div>
  </div>
);

export default function App() {
  const [page, setPage] = useState<Page>("summary");
  const [cap, setCap] = useState<Capabilities>();
  const [capError, setCapError] = useState("");
  const loadCap = () => {
    setCapError("");
    void api
      .capabilities()
      .then(setCap)
      .catch((e) =>
        setCapError(
          `Capability incompatible or server unavailable: ${e.message}`,
        ),
      );
  };
  useEffect(() => {
    loadCap();
  }, []);
  const backendTone = capError ? "bad" : cap ? "ok" : "warn";
  const backendLabel = capError
    ? "Backend unavailable"
    : cap
      ? "Backend online"
      : "Connecting";
  return (
    <div className="app">
      <div className="shell">
        <header className="app-header">
          <div className="brand">
            <p className="eyebrow">NANEXUS / COMMUNITY</p>
            <h1 className="app-title">Nanexus AI Video Summary</h1>
            <p className="subtitle">
              Daily summaries, semantic search, and cited chat over stored
              camera events.
            </p>
          </div>
          <div className="header-status">
            <Pill tone={backendTone} dot>
              {backendLabel}
            </Pill>
            {cap && <Pill>API {cap.api_version}</Pill>}
          </div>
        </header>
        <nav className="tabs" role="tablist" aria-label="Application sections">
          {PAGES.map((item) => (
            <button
              key={item.id}
              className="tab"
              type="button"
              role="tab"
              aria-selected={page === item.id}
              onClick={() => setPage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <main className="content">
          {capError && <State error={capError} retry={loadCap} />}
          {!cap && !capError ? (
            <State loading />
          ) : cap && !compatible(cap) ? (
            <State error="Incompatible server: Video API v1, capability/schema/processor v1 and UUID subjects are required." />
          ) : page === "summary" ? (
            <SummaryPage enabled={!!cap?.summary.available} />
          ) : page === "search" ? (
            <SearchPage enabled={!!cap?.search.available} />
          ) : page === "chat" ? (
            <ChatPage enabled={!!cap?.chat.available} />
          ) : page === "status" ? (
            <Status />
          ) : (
            <Settings cap={cap} />
          )}
        </main>
      </div>
    </div>
  );
}

function SummaryPage({ enabled }: { enabled: boolean }) {
  const [data, setData] = useState<Summary | null>();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const load = () => {
    setLoading(true);
    setError("");
    api
      .summary(
        new Date().toISOString().slice(0, 10),
        Intl.DateTimeFormat().resolvedOptions().timeZone,
      )
      .then((x) => setData(x.summary))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    if (enabled) load();
  }, [enabled]);
  if (!enabled)
    return <State error="Summary is not supported by this server." />;
  const highlights = data?.structured_content?.highlights ?? [];
  const byLabel = data?.structured_content?.by_label;
  return (
    <section>
      <PageHead title="Summary">
        Precomputed daily overview of stored camera events.
      </PageHead>
      <State
        loading={loading}
        error={error}
        empty={
          data === null ? "No precomputed summary for this day." : undefined
        }
        retry={load}
      />
      {data && (
        <div className="stack">
          <article className="panel">
            <div className="meta-row">
              <h3 className="result-title">{data.local_date}</h3>
              {data.timezone && <span className="muted">{data.timezone}</span>}
              {data.status && <Pill>{data.status}</Pill>}
            </div>
            <p className="helper generator">
              {data.generator}
              {data.structured_content?.review_count != null
                ? ` · ${data.structured_content.review_count} reviews`
                : ""}
            </p>
            {byLabel && Object.keys(byLabel).length > 0 && (
              <div className="meta-row label-row">
                {Object.entries(byLabel).map(([label, count]) => (
                  <Pill key={label} tone="label">
                    {`${label} ${count}`}
                  </Pill>
                ))}
              </div>
            )}
            <p className="prose">{data.content}</p>
          </article>
          {highlights.length > 0 && (
            <article className="panel">
              <p className="section-label">Highlights</p>
              <div className="highlight-list">
                {highlights.map((item, index) => (
                  <HighlightItem item={item} key={item.subject_id ?? index} />
                ))}
              </div>
            </article>
          )}
          {data.source_subject_ids.length > 0 && (
            <article className="panel">
              <p className="section-label">Source subjects</p>
              <div className="subject-list">
                {data.source_subject_ids.map((id) => (
                  <Subject id={id} key={id} />
                ))}
              </div>
            </article>
          )}
        </div>
      )}
    </section>
  );
}

function HighlightItem({ item }: { item: SummaryHighlight }) {
  const title =
    item.caption || item.labels?.join(" / ") || item.camera || "Highlight";
  return (
    <div className="card highlight-card">
      <div className="highlight-top">
        <p className="highlight-title">{title}</p>
        <span className="when">{compactTime(item.time)}</span>
      </div>
      <div className="meta-row">
        {item.camera && <Pill tone="label">{item.camera}</Pill>}
        {item.labels?.map((label) => (
          <Pill key={label}>{label}</Pill>
        ))}
        {item.repeat_count != null && item.repeat_count > 1 && (
          <span className="muted">x{item.repeat_count}</span>
        )}
      </div>
      {item.subject_id && <Subject id={item.subject_id} />}
    </div>
  );
}

function SearchPage({ enabled }: { enabled: boolean }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[]>();
  const [error, setError] = useState("");
  const [degraded, setDegraded] = useState("");
  const [method, setMethod] = useState("");
  const [total, setTotal] = useState<number>();
  const run = () => {
    setError("");
    api
      .search(q)
      .then((x: SearchResponse) => {
        setHits(x.items);
        setDegraded(
          x.degraded ? (x.degradation_reason ?? "Search degraded") : "",
        );
        setMethod(x.method ?? "");
        setTotal(x.total);
      })
      .catch((e) => setError(e.message));
  };
  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (q.trim()) run();
  };
  if (!enabled)
    return <State error="Search is not supported by this server." />;
  return (
    <section>
      <PageHead title="Search">
        Query stored events and inspect subject, score, and evidence metadata.
      </PageHead>
      <form className="panel stack" onSubmit={onSubmit}>
        <div className="field">
          <label className="field-label" htmlFor="search-query">
            Query
          </label>
          <div className="search-bar">
            <input
              id="search-query"
              aria-label="query"
              value={q}
              placeholder="person, vehicle, camera activity…"
              onChange={(e) => setQ(e.target.value)}
            />
            <button
              className="btn btn-primary"
              type="submit"
              disabled={!q.trim()}
            >
              Search
            </button>
          </div>
        </div>
        {(method || total != null) && (
          <div className="meta-row">
            {method && <Pill>{method}</Pill>}
            {total != null && (
              <span className="muted">
                {total} result{total === 1 ? "" : "s"}
              </span>
            )}
          </div>
        )}
      </form>
      {degraded && (
        <p className="state-box warn block-gap">
          <Pill tone="warn">Degraded</Pill> {degraded}
        </p>
      )}
      <div className="stack block-gap">
        <State
          error={error}
          empty={hits?.length === 0 ? "No matching events." : undefined}
          retry={run}
        />
        {hits?.map((h) => (
          <article className="card result-card" key={h.subject_id}>
            <div className="result-top">
              <p className="result-title">{h.camera ?? "Event"}</p>
              <span className="score">{h.score.toFixed(2)}</span>
            </div>
            <div className="meta-row">
              {h.site && <span className="muted">{h.site}</span>}
              {h.occurred_at && (
                <span className="when">{compactTime(h.occurred_at)}</span>
              )}
              {h.labels.map((label) => (
                <Pill key={label} tone="label">
                  {label}
                </Pill>
              ))}
            </div>
            <Subject id={h.subject_id} />
            {h.evidence && h.evidence.length > 0 && (
              <div className="subject-list">
                {h.evidence.map((href, index) => (
                  <a key={href} href={href} target="_blank" rel="noreferrer">
                    {h.evidence && h.evidence.length > 1
                      ? `Evidence ${index + 1}`
                      : "Evidence"}
                  </a>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function ChatPage({ enabled }: { enabled: boolean }) {
  const owner = "web-local";
  const [q, setQ] = useState("");
  const [job, setJob] = useState<ChatJob>();
  const [error, setError] = useState("");
  const submit = async () => {
    setError("");
    try {
      let next = await api.chat(q, owner, job?.conversation_id);
      setJob(next);
      for (
        let i = 0;
        i < 30 && !["completed", "failed"].includes(next.status);
        i++
      ) {
        await new Promise((r) => setTimeout(r, 1000));
        next = await api.job(next.id, owner);
        setJob(next);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (q.trim()) void submit();
  };
  if (!enabled) return <State error="Chat is not supported by this server." />;
  const answer = job?.answer;
  const pending = job && !answer && !error;
  return (
    <section>
      <PageHead title="Chat">
        Ask about events, summaries, vehicles, and activity already stored by
        the application.
      </PageHead>
      <form className="panel" onSubmit={onSubmit}>
        <div className="field">
          <label className="field-label" htmlFor="chat-question">
            Question
          </label>
          <div className="composer">
            <textarea
              id="chat-question"
              aria-label="question"
              value={q}
              rows={2}
              placeholder="Ask about events, summaries, vehicles, activity…"
              onChange={(e) => setQ(e.target.value)}
            />
            <button
              className="btn btn-primary"
              type="submit"
              disabled={!q.trim()}
            >
              Ask
            </button>
          </div>
        </div>
      </form>
      <div className="stack block-gap">
        {pending && (
          <p className="state-box" role="status">
            Job {job.status}…
          </p>
        )}
        <State error={error} retry={() => void submit()} />
        {answer && (
          <article className="panel answer-card">
            <div className="answer-head">
              <h3 className="answer-title">Answer</h3>
              <div className="meta-row">
                {answer.degraded && <Pill tone="warn">Fallback mode</Pill>}
                {answer.method && <Pill>{answer.method}</Pill>}
              </div>
            </div>
            {(answer.error_code || job.status) && (
              <p className="technical-meta faint">
                {answer.error_code && <span>{answer.error_code}</span>}
                {answer.error_code && job.status ? <span>·</span> : null}
                {job.status && <span>{job.status}</span>}
              </p>
            )}
            <p className="prose answer-body">{answer.content}</p>
            {answer.citations.length > 0 && (
              <div className="citation-list">
                <p className="section-label">Citations</p>
                {answer.citations.map((c) => (
                  <Subject key={c.subject_id} id={c.subject_id} />
                ))}
              </div>
            )}
          </article>
        )}
      </div>
    </section>
  );
}

function Status() {
  const [x, setX] = useState<Awaited<ReturnType<typeof api.health>>>();
  const [e, setE] = useState("");
  const load = () => {
    setE("");
    void api
      .health()
      .then(setX)
      .catch((v) => setE(v.message));
  };
  useEffect(() => {
    load();
  }, []);
  return (
    <section>
      <PageHead title="Status">
        Processor and model observability for this Video Summary instance.
      </PageHead>
      <State error={e} retry={load} />
      {x && (
        <div className="stack">
          <div className="status-grid">
            <article className="panel status-card">
              <span className="status-label">status</span>
              <span className={`status-value${x.status === "ok" ? " ok" : ""}`}>
                {x.status}
              </span>
            </article>
            <article className="panel status-card">
              <span className="status-label">database</span>
              <span className="status-value">{String(x.database)}</span>
            </article>
            <article className="panel status-card">
              <span className="status-label">queue</span>
              <span className="status-value">{String(x.redis)}</span>
            </article>
            <article className="panel status-card">
              <span className="status-label">model_provider</span>
              <span className="status-value">provider {x.model_provider}</span>
            </article>
            <article className="panel status-card">
              <span className="status-label">legacy ai_mode</span>
              <span className="status-value">legacy ai {x.ai_mode}</span>
              <p className="legacy-note">
                Compatibility metadata only. Do not infer the v1 provider from
                this field.
              </p>
            </article>
            <article className="panel status-card">
              <span className="status-label">summary_mode</span>
              <span className="status-value">{x.summary_mode}</span>
            </article>
            <article className="panel status-card">
              <span className="status-label">chat_mode</span>
              <span className="status-value">{x.chat_mode}</span>
            </article>
          </div>
        </div>
      )}
    </section>
  );
}

function Settings({ cap }: { cap?: Capabilities }) {
  return (
    <section>
      <PageHead title="Settings">
        Local client contract details. No additional runtime controls are
        exposed here.
      </PageHead>
      <div className="stack">
        <article className="panel">
          <p className="section-label">Connection</p>
          <p className="prose">
            API origin: same origin (configure the reverse proxy; no internal
            URL or token is exposed).
          </p>
        </article>
        <article className="panel">
          <p className="section-label">API contract</p>
          <div className="settings-grid">
            <div className="setting-block">
              <span className="setting-label">Subject IDs</span>
              <span className="setting-value">
                {cap?.subject_reference ?? "checking"}
              </span>
            </div>
            <div className="setting-block">
              <span className="setting-label">API</span>
              <span className="setting-value">
                {cap?.api_version ?? "checking"}
              </span>
            </div>
            <div className="setting-block">
              <span className="setting-label">Capability</span>
              <span className="setting-value">
                {cap?.capability_version ?? "checking"}
              </span>
            </div>
            <div className="setting-block">
              <span className="setting-label">Schema</span>
              <span className="setting-value">
                {cap?.canonical_schema_version ?? "checking"}
              </span>
            </div>
          </div>
        </article>
        <article className="panel">
          <p className="section-label">Ownership</p>
          <p className="prose">
            Ownership authentication:{" "}
            {cap?.ownership_authentication ?? "checking"} (the local owner key
            is isolation only, not production authentication).
          </p>
        </article>
        <article className="panel">
          <p className="section-label">Compatibility</p>
          <p className="prose">
            Legacy fallback: {String(cap?.legacy_fallback_available ?? false)}
          </p>
        </article>
      </div>
    </section>
  );
}
