import { useDeferredValue, useEffect, useState, useTransition } from "react";
import { Link, useSearchParams } from "react-router";

import { EmptyState } from "../components/EmptyState";
import { Pill } from "../components/Pill";
import { SectionCard } from "../components/SectionCard";
import { api, type DueReview, type Question } from "../lib/api";
import { masteryTone, practiceHref } from "../lib/format";

export function ReviewPage() {
  const [searchParams] = useSearchParams();
  const [dueReviews, setDueReviews] = useState<DueReview[]>([]);
  const [keyword, setKeyword] = useState("");
  const [moduleName, setModuleName] = useState(searchParams.get("module") || "");
  const [results, setResults] = useState<Question[]>([]);
  const [dueError, setDueError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const deferredKeyword = useDeferredValue(keyword);

  useEffect(() => {
    setModuleName(searchParams.get("module") || "");
  }, [searchParams]);

  async function loadDueReviews() {
    setDueError(null);
    try {
      const body = await api.dueReviews(50);
      startTransition(() => {
        setDueReviews(body.reviews);
      });
    } catch (error) {
      setDueError(error instanceof Error ? error.message : "加载到期复习失败。");
    }
  }

  async function searchQuestions() {
    const safeKeyword = keyword.trim();
    if (!safeKeyword) {
      setSearchError("请输入关键词");
      return;
    }
    setSearchError(null);
    try {
      const body = await api.searchQuestions(
        safeKeyword,
        moduleName.trim() || undefined,
      );
      startTransition(() => {
        setResults(body.questions);
      });
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "搜索失败。");
    }
  }

  useEffect(() => {
    void loadDueReviews();
  }, []);

  return (
    <div className="page-grid">
      <SectionCard
        eyebrow="Review Center"
        title="先清理到期清单，再精确检索题库"
        description="复习页保留题库入口，但把真正优先级更高的内容放到最上面。"
        action={
          <button type="button" className="button button--primary" onClick={() => void loadDueReviews()}>
            {isPending ? "刷新中..." : "刷新到期列表"}
          </button>
        }
      >
        <div className="status-strip">
          <span>支持从仪表盘带 `module` 参数跳入，自动预填模块过滤条件。</span>
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Due Queue"
        title="到期复习"
        description={`当前共 ${dueReviews.length} 道待处理题目。`}
      >
        {dueReviews.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>题目</th>
                  <th>模块</th>
                  <th>掌握度</th>
                  <th>下次复习</th>
                  <th>逾期</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {dueReviews.map((review) => (
                  <tr key={review.question_id}>
                    <td>{review.title || review.question_id}</td>
                    <td>{review.module || "-"}</td>
                    <td>
                      <Pill tone={masteryTone(review.mastery_level)}>
                        {review.mastery_level || "未知"}
                      </Pill>
                    </td>
                    <td>{review.next_review || "-"}</td>
                    <td>
                      <Pill tone={Number(review.days_overdue || 0) > 0 ? "bad" : "ok"}>
                        {Number(review.days_overdue || 0) > 0
                          ? `${review.days_overdue} 天`
                          : "今日"}
                      </Pill>
                    </td>
                    <td>
                      <Link to={practiceHref(review.question_id, review.module)}>
                        去练习
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="没有到期复习"
            description={dueError || "今天暂时不用回顾旧题，可以主动查找新题。"}
          />
        )}
      </SectionCard>

      <SectionCard
        eyebrow="Knowledge Search"
        title="题库检索"
        description="按关键词和模块组合检索，搜到后可直接跳转到面试页。"
        tone="signal"
        action={
          <button type="button" className="button button--primary" onClick={() => void searchQuestions()}>
            搜索题目
          </button>
        }
      >
        <div className="field-grid">
          <label className="field">
            <span>关键词</span>
            <input
              value={keyword}
              placeholder="如 HashMap、线程池、volatile"
              onChange={(event) => setKeyword(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void searchQuestions();
                }
              }}
            />
          </label>
          <label className="field">
            <span>模块（可选）</span>
            <input
              value={moduleName}
              placeholder="如 Java基础"
              onChange={(event) => setModuleName(event.target.value)}
            />
          </label>
        </div>

        <div className="status-strip">
          <span>
            {deferredKeyword
              ? `准备检索：${deferredKeyword}`
              : "输入关键词后按 Enter 或点击“搜索题目”"}
          </span>
          {searchError ? <Pill tone="bad">{searchError}</Pill> : null}
        </div>

        {results.length ? (
          <div className="stack-list">
            {results.map((question) => (
              <article key={question.question_id} className="list-row">
                <div>
                  <div>
                    <Pill>{question.module || "未知模块"}</Pill>
                    <strong>{question.title || question.question_id}</strong>
                  </div>
                  <div className="list-row__meta">
                    question_id={question.question_id}
                  </div>
                </div>
                <Link to={practiceHref(question.question_id, question.module)}>
                  去练习
                </Link>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="题库搜索结果会显示在这里"
            description="先输入关键词；如果没有命中，换一个更具体的术语试试。"
          />
        )}
      </SectionCard>
    </div>
  );
}
