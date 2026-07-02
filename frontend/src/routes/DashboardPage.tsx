import { Link } from "react-router";
import { useEffect, useState, useTransition } from "react";

import { EmptyState } from "../components/EmptyState";
import { Pill } from "../components/Pill";
import { ProgressBar } from "../components/ProgressBar";
import { SectionCard } from "../components/SectionCard";
import { StatTile } from "../components/StatTile";
import { api, type DueReview, type OverviewStats } from "../lib/api";
import { percentage, practiceHref } from "../lib/format";

export function DashboardPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [weakModules, setWeakModules] = useState<string[]>([]);
  const [dueReviews, setDueReviews] = useState<DueReview[]>([]);
  const [serviceHealthy, setServiceHealthy] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function loadAll() {
    setErrorMessage(null);
    try {
      const [health, overviewBody, weakBody, dueBody] = await Promise.all([
        api.health(),
        api.statsOverview(),
        api.weakModules(5),
        api.dueReviews(20),
      ]);
      startTransition(() => {
        setServiceHealthy(health.status === "ok");
        setOverview(overviewBody);
        setWeakModules(weakBody.modules);
        setDueReviews(dueBody.reviews);
      });
    } catch (error) {
      setServiceHealthy(false);
      setErrorMessage(error instanceof Error ? error.message : "加载仪表盘失败。");
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  return (
    <div className="page-grid">
      <SectionCard
        eyebrow="Mission Control"
        title="今天先做什么，一眼就能定下来"
        description="把掌握率、薄弱模块和到期复习放在同一块视野里，不再在多个页面之间来回跳。"
        tone="ink"
        action={
          <div className="button-row">
            <button type="button" className="button button--primary" onClick={() => void loadAll()}>
              {isPending ? "刷新中..." : "刷新数据"}
            </button>
            <Link className="button button--ghost" to="/interview">
              去做面试
            </Link>
            <Link className="button button--ghost" to="/review">
              去复习
            </Link>
          </div>
        }
      >
        <div className="status-strip">
          <Pill tone={serviceHealthy === true ? "ok" : serviceHealthy === false ? "bad" : "neutral"}>
            {serviceHealthy === true ? "服务正常" : serviceHealthy === false ? "服务异常" : "服务状态未知"}
          </Pill>
          <span>当前页来自新的 React 前端工程，而不是手写静态 HTML 联调页。</span>
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Overview"
        title="整体进度"
        description="数据来自学习记录和题目元数据，帮助你判断整体节奏是否健康。"
      >
        {overview ? (
          <>
            <div className="stat-grid">
              <StatTile label="题目总数" value={overview.total} />
              <StatTile label="已掌握" value={overview.mastered} />
              <StatTile label="复习中" value={overview.reviewing} />
              <StatTile label="学习中" value={overview.learning} />
              <StatTile label="未开始" value={overview.untouched} />
              <StatTile label="今日练习" value={overview.today_count} />
            </div>
            <ProgressBar
              label="掌握率"
              value={percentage(overview.mastery_rate)}
            />
          </>
        ) : (
          <EmptyState
            title="还没有概览数据"
            description={errorMessage || "初始化题库后，这里会出现整体进度。"}
          />
        )}
      </SectionCard>

      <SectionCard
        eyebrow="Weak Modules"
        title="薄弱模块 Top"
        description="把精力用在最值得补的地方。"
      >
        {weakModules.length ? (
          <div className="stack-list">
            {weakModules.map((module, index) => (
              <Link
                key={module}
                className="list-row list-row--link"
                to={`/review?module=${encodeURIComponent(module)}`}
              >
                <span>
                  <Pill tone="bad">#{index + 1}</Pill>
                  <strong>{module}</strong>
                </span>
                <span>去复习</span>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            title="暂无薄弱模块"
            description="还没有足够的答题记录，先抽几道题再回来。"
          />
        )}
      </SectionCard>

      <SectionCard
        eyebrow="Due Queue"
        title="今日到期复习"
        description="到期题目优先回看，别让遗忘曲线把你打回原点。"
        tone="signal"
      >
        {dueReviews.length ? (
          <div className="stack-list">
            {dueReviews.map((review) => (
              <Link
                key={review.question_id}
                className="list-row list-row--link"
                to={practiceHref(review.question_id, review.module)}
              >
                <div>
                  <strong>{review.title || review.question_id}</strong>
                  <div className="list-row__meta">
                    {review.module} · next_review={review.next_review || "-"}
                  </div>
                </div>
                <Pill tone={Number(review.days_overdue || 0) > 0 ? "bad" : "ok"}>
                  {Number(review.days_overdue || 0) > 0
                    ? `逾期 ${review.days_overdue} 天`
                    : "今日"}
                </Pill>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            title="今日无到期复习"
            description="可以把时间投入新题，或者从薄弱模块里主动挑题。"
          />
        )}
      </SectionCard>
    </div>
  );
}
