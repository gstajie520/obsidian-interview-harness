import { Link } from "react-router";

import { EmptyState } from "../EmptyState";
import { Pill } from "../Pill";
import type { OrchestrationRun } from "../../lib/api";

interface RunHistoryListProps {
  runs: OrchestrationRun[];
}

export function RunHistoryList({ runs }: RunHistoryListProps) {
  if (!runs.length) {
    return (
      <EmptyState
        title="暂无闭环历史"
        description="创建会话并提交答案后，这里会出现与当前题目相关的编排记录。"
      />
    );
  }

  return (
    <div className="history-list">
      {runs.map((run) => (
        <article key={run.id} className="history-card">
          <div className="history-card__top">
            <div>
              <Pill>run #{run.id}</Pill>
              <strong>{run.question_id}</strong>
            </div>
            <Pill>{run.report_type || "daily"}</Pill>
          </div>
          <div className="history-card__meta">
            session={run.session_id || "-"} · status={run.status}
          </div>
          <pre className="json-block">
            {JSON.stringify(run.payload, null, 2)}
          </pre>
          <div className="history-card__actions">
            <Link to={`/interview?question_id=${encodeURIComponent(run.question_id)}`}>
              重新打开题目
            </Link>
          </div>
        </article>
      ))}
    </div>
  );
}
