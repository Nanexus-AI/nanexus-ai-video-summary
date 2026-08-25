import { useEffect, useState } from "react";
import {
  api,
  Capabilities,
  ChatJob,
  SearchHit,
  Summary,
  subjectHref,
} from "./api";
import "./styles.css";
type Page = "summary" | "search" | "chat" | "status" | "settings";
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
    <p role="status">Loading…</p>
  ) : error ? (
    <div role="alert">
      <p>{error}</p>
      {retry && <button onClick={retry}>Retry</button>}
    </div>
  ) : empty ? (
    <p>{empty}</p>
  ) : null;
const Subject = ({ id }: { id: string }) => (
  <a href={subjectHref(id)} target="_blank" rel="noreferrer">
    Related event {id.slice(0, 8)}
  </a>
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
  return (
    <main>
      <header>
        <h1>Nanexus Video Summary</h1>
        <nav>
          {(["summary", "search", "chat", "status", "settings"] as Page[]).map(
            (p) => (
              <button key={p} onClick={() => setPage(p)}>
                {p}
              </button>
            ),
          )}
        </nav>
      </header>
      {capError && <State error={capError} retry={loadCap} />}{" "}
      {cap && cap.subject_reference !== "uuid" ? (
        <State error="Incompatible server: UUID subject references are required." />
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
  return (
    <section>
      <h2>Summary</h2>
      <State
        loading={loading}
        error={error}
        empty={
          data === null ? "No precomputed summary for this day." : undefined
        }
        retry={load}
      />
      {data && (
        <>
          <p>{data.content}</p>
          <small>
            {data.generator} · {data.local_date}
          </small>
          <div>
            {data.source_subject_ids.map((id) => (
              <Subject id={id} key={id} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
function SearchPage({ enabled }: { enabled: boolean }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[]>();
  const [error, setError] = useState("");
  const [degraded, setDegraded] = useState("");
  const run = () => {
    setError("");
    api
      .search(q)
      .then((x) => {
        setHits(x.items);
        setDegraded(
          x.degraded ? (x.degradation_reason ?? "Search degraded") : "",
        );
      })
      .catch((e) => setError(e.message));
  };
  if (!enabled)
    return <State error="Search is not supported by this server." />;
  return (
    <section>
      <h2>Search</h2>
      <input
        aria-label="query"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <button disabled={!q.trim()} onClick={run}>
        Search
      </button>
      {degraded && <p className="warn">{degraded}</p>}
      <State
        error={error}
        empty={hits?.length === 0 ? "No matching events." : undefined}
        retry={run}
      />
      {hits?.map((h) => (
        <article key={h.subject_id}>
          <p>
            {h.camera ?? "Event"} · {h.labels.join(", ")} · {h.score.toFixed(2)}
          </p>
          <Subject id={h.subject_id} />
        </article>
      ))}
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
  if (!enabled) return <State error="Chat is not supported by this server." />;
  return (
    <section>
      <h2>Chat</h2>
      <textarea
        aria-label="question"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <button disabled={!q.trim()} onClick={submit}>
        Ask
      </button>
      {job && !job.answer && <p role="status">Job {job.status}…</p>}
      <State error={error} retry={submit} />
      {job?.answer && (
        <article>
          {job.answer.degraded && (
            <p className="warn">
              Degraded answer ({job.answer.error_code ?? "fallback"})
            </p>
          )}
          <p>{job.answer.content}</p>
          {job.answer.citations.map((c) => (
            <Subject key={c.subject_id} id={c.subject_id} />
          ))}
        </article>
      )}
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
      <h2>Processor / Model status</h2>
      <State error={e} retry={load} />
      {x && (
        <p className={x.status === "ok" ? "" : "warn"}>
          {x.status} · database {String(x.database)} · queue {String(x.redis)} ·
          model {x.ai_mode} · summary {x.summary_mode} · chat {x.chat_mode}
        </p>
      )}
    </section>
  );
}
function Settings({ cap }: { cap?: Capabilities }) {
  return (
    <section>
      <h2>Settings</h2>
      <p>
        API origin: same origin (configure the reverse proxy; no internal URL or
        token is exposed).
      </p>
      <p>
        Subject IDs: {cap?.subject_reference ?? "checking"} · API{" "}
        {cap?.api_version ?? "checking"}
      </p>
      <p>
        Ownership authentication: {cap?.ownership_authentication ?? "checking"}{" "}
        (the local owner key is isolation only, not production authentication).
      </p>
      <p>Legacy fallback: {String(cap?.legacy_fallback_available ?? false)}</p>
    </section>
  );
}
