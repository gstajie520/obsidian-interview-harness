import { Pill } from "../Pill";
import { EmptyState } from "../EmptyState";
import { scoreTone } from "../../lib/format";
import type { EvaluationCompleteMessage } from "../../lib/api";

interface ResultSummaryProps {
  result: EvaluationCompleteMessage | null;
}

export function ResultSummary({ result }: ResultSummaryProps) {
  if (!result) {
    return (
      <EmptyState
        title="还没有本次结果"
        description="提交答案后，这里会展示四维评分、弱点和多 Agent 编排摘要。"
      />
    );
  }

  if (result.status !== "success") {
    return (
      <EmptyState
        title="本次提交未成功"
        description={result.message || "服务端返回了错误状态。"}
      />
    );
  }

  const scores = result.scores || {};
  const weakPoints = result.weak_points || [];
  const orchestration = result.orchestration;

  if (!orchestration || result.overall_score === undefined) {
    return (
      <EmptyState
        title="结果结构不完整"
        description="服务端返回了 success，但缺少前端渲染所需字段。"
      />
    );
  }

  return (
    <div className="result-stack">
      <div className="score-row">
        {Object.entries(scores).map(([key, value]) => (
          <Pill key={key} tone={scoreTone(value)}>
            {key}: {value}
          </Pill>
        ))}
        <Pill tone={scoreTone(result.overall_score)}>
          overall: {result.overall_score.toFixed(2)}
        </Pill>
      </div>

      <div className="detail-grid">
        <div className="detail-card">
          <div className="detail-card__label">弱点</div>
          <ul>
            {weakPoints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="detail-card">
          <div className="detail-card__label">闭环摘要</div>
          <dl className="detail-list">
            <div>
              <dt>run_id</dt>
              <dd>{orchestration.run_id}</dd>
            </div>
            <div>
              <dt>report</dt>
              <dd>{orchestration.recommendation.report_type || "-"}</dd>
            </div>
            <div>
              <dt>events</dt>
              <dd>{orchestration.events}</dd>
            </div>
            <div>
              <dt>next_review</dt>
              <dd>{orchestration.schedule.next_review || "-"}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
