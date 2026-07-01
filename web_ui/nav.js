/*
 * 顶部导航注入脚本。
 *
 * 静态站点没有模板引擎（不像 Thymeleaf / JSP 那样可以 include 公共片段），
 * 所以这里用一个小脚本，在每个页面运行时动态插入统一的导航条。
 *
 * 用法：页面在 <body> 顶部放一个 <div id="nav-root" data-active="dashboard"></div>，
 * data-active 用来标记当前页高亮哪个菜单项。
 */
(function () {
  // 站点内的四个主页面。每一项类似 Java 里的一个不可变常量记录。
  const LINKS = [
    { key: "dashboard", href: "dashboard.html", label: "仪表盘" },
    { key: "interview", href: "index.html", label: "面试" },
    { key: "review", href: "review.html", label: "复习" },
    { key: "stats", href: "stats.html", label: "统计" },
  ];

  function buildNav(active) {
    const nav = document.createElement("nav");
    nav.className = "nav panel";

    const brand = document.createElement("span");
    brand.className = "brand";
    brand.textContent = "AI 面试陪练";
    nav.appendChild(brand);

    // 遍历菜单项，逐个生成 <a>；当前页加 active 类高亮。
    for (const link of LINKS) {
      const a = document.createElement("a");
      a.href = link.href;
      a.textContent = link.label;
      if (link.key === active) {
        a.className = "active";
      }
      nav.appendChild(a);
    }
    return nav;
  }

  window.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("nav-root");
    if (!root) {
      return;
    }
    const active = root.getAttribute("data-active") || "";
    root.replaceWith(buildNav(active));
  });
})();
