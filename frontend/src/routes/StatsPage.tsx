import { useEffect, useState, useTransition } from "react";
import { Link } from "react-router";

import { EmptyState } from "../components/EmptyState";
import { Pill } from "../components/Pill";
import { ProgressBar } from "../components/ProgressBar";
import { SectionCard } from "../components/SectionCard";
import { StatTile } from "../components/StatTile";
import { api, type OverviewStats } from "../lib/api";

const DIST_FIELDS = [
  { key: "mastered", label: "已掌握", tone: "ok" as const },
  { key: "reviewing", label: "复习中", tone: "warn" as const },
  { key: "learning", label: "学习中", tone: "warn" as const },
  { key: "untouched", label: "未开始", tone: "bad" as const },
];

export function StatsPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [weakModules, setWeakModules] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function loadAll() {
    setErrorMessage(null);
    try {
      const [overviewBody, weakBody] = await Promise.all([
        api.statsOverview(),
        api.weakModules(10),
      ]);
      startTransition(() => {
        setOverview(overviewBody);
        setWeakModules(weakBody.modules);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "统计加载失败。");
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  return (
    <div className="page-grid">
      <SectionCard
        eyebrow="Metrics"
        title="统计页只看长期变化"
        description="仪表盘回答“今天做什么”，统计页回答“最近整体有没有往对的方向走”。"
        action={
          <button type="button" className="button button--primary" onClick={() => void loadAll()}>
            {isPending ? "刷新中..." : "刷新数据"}
          </button>
        }
      >
        <div className="status-strip">
          <span>这里强调分布、比例和弱项排序，不再混入当前会话的操作按钮。</span>
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Topline"
        title="关键指标"
        description="保留最能说明问题的指标，不让卡片泛滥。"
      >
        {overview ? (
          <div className="stat-grid stat-grid--compact">
            <StatTile label="题目总数" value={overview.total} />
            <StatTile label="今日练习" value={overview.today_count} />
            <StatTile
              label="掌握率"
              value={`${Math.round(overview.mastery_rate * 100)}%`}
            />
          </div>
        ) : (
          <EmptyState
            title="暂无统计数据"
            description={errorMessage || "先跑一轮面试流程，再回来查看。"}
          />
        )}
      </SectionCard>

      <SectionCard
        eyebrow="Distribution"
        title="掌握度分布"
        description="直接看每一档占总题量的比例，不需要猜测。"
        tone="signal"
      >
        {overview ? (
          <div className="stack-list">
            {DIST_FIELDS.map((field) => {
              const count = overview[field.key as keyof OverviewStats] as number;
              const percent =
                overview.total > 0 ? Math.round((count / overview.total) * 100) : 0;
              return (
                <div key={field.key} className="distribution-row">
                  <div className="distribution-row__head">
                    <Pill tone={field.tone}>{field.label}</Pill>
                    <span>
                      {count} 题 · {percent}%
                    </span>
                  </div>
                  <ProgressBar label={field.label} value={percent} />
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            title="掌握度分布暂不可用"
            description={errorMessage || "等待统计接口返回数据。"}
          />
        )}
      </SectionCard>

      <SectionCard
        eyebrow="Weak Ranking"
        title="薄弱模块排序"
        description="按平均分升序排列，方便你把复习时间压在最值得补的地方。"
      >
        {weakModules.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>模块</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {weakModules.map((module, index) => (
                  <tr key={module}>
                    <td>{index + 1}</td>
                    <td>{module}</td>
                    <td>
                      <Link to={`/review?module=${encodeURIComponent(module)}`}>
                        去复习
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="暂无薄弱模块排序"
            description="记录量不足时，这里会保持空白。"
          />
        )}
      </SectionCard>
    </div>
  );
}
