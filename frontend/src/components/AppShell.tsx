import { NavLink, Outlet } from "react-router";

import { cn } from "../lib/format";

const NAV_ITEMS = [
  {
    to: "/dashboard",
    label: "仪表盘",
    summary: "今日节奏与总体进度",
  },
  {
    to: "/interview",
    label: "面试",
    summary: "实时答题与闭环反馈",
  },
  {
    to: "/review",
    label: "复习",
    summary: "到期清单与题库检索",
  },
  {
    to: "/stats",
    label: "统计",
    summary: "掌握分布与薄弱模块",
  },
];

const dateFormatter = new Intl.DateTimeFormat("zh-CN", {
  month: "long",
  day: "numeric",
  weekday: "short",
});

export function AppShell() {
  const todayLabel = dateFormatter.format(new Date());
  const brandMarkUrl = `${import.meta.env.BASE_URL}brand-mark.svg`;

  return (
    <div className="shell">
      <aside className="shell__aside">
        <div className="brand-panel">
          <div className="brand-panel__eyebrow">Study Lab</div>
          <div className="brand-panel__hero">
            <img
              className="brand-panel__mark"
              src={brandMarkUrl}
              alt="AI 面试陪练品牌标识"
            />
            <div>
              <h1>AI 面试陪练</h1>
              <p>
                把面试训练、薄弱点分析、复习编排和反馈闭环压缩到一套前端工程里。
              </p>
            </div>
          </div>
          <div className="brand-panel__meta">
            <span>{todayLabel}</span>
            <span>FastAPI / React / Vite</span>
          </div>
        </div>

        <nav className="nav-rail" aria-label="主导航">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn("nav-rail__link", isActive && "nav-rail__link--active")
              }
            >
              <span className="nav-rail__label">{item.label}</span>
              <span className="nav-rail__summary">{item.summary}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="shell__main">
        <Outlet />
      </main>
    </div>
  );
}
