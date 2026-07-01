/*
 * 前端公共 API 封装。
 *
 * 把 fetch 调用集中在一个文件，类似 Java 里抽出一个 ApiClient 工具类：
 * 页面只关心“要哪个数据”，不用每次都重复写 fetch、状态码判断、JSON 解析。
 */
const API = (function () {
  // 空字符串表示与页面同源，前端和后端由同一个 FastAPI 服务托管。
  const baseUrl = "";

  async function request(path, options = {}) {
    const resp = await fetch(baseUrl + path, options);
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${text}`);
    }
    return resp.json();
  }

  return {
    request,
    health: () => request("/api/health"),
    statsOverview: () => request("/api/stats/overview"),
    weakModules: (limit = 10) => request(`/api/stats/weak-modules?limit=${limit}`),
    dueReviews: (limit = 50) => request(`/api/stats/due-reviews?limit=${limit}`),
    randomQuestion: (module) =>
      request(
        module
          ? `/api/questions/random?module=${encodeURIComponent(module)}`
          : "/api/questions/random"
      ),
    searchQuestions: (keyword, module) => {
      const params = new URLSearchParams();
      params.set("keyword", keyword);
      if (module) {
        params.set("module", module);
      }
      return request(`/api/questions/search?${params.toString()}`);
    },
    orchestrationRuns: (params = {}) => {
      const query = new URLSearchParams();
      if (params.session_id) query.set("session_id", params.session_id);
      if (params.question_id) query.set("question_id", params.question_id);
      query.set("limit", String(params.limit || 20));
      return request(`/api/orchestration/runs?${query.toString()}`);
    },
    createSession: (primaryAgent = "interviewer") =>
      request("/api/session/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ primary_agent: primaryAgent }),
      }),
  };
})();
