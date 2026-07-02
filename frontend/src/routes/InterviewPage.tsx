import { useEffect, useRef, useState, useTransition } from "react";
import { useSearchParams } from "react-router";

import { EmptyState } from "../components/EmptyState";
import { Pill } from "../components/Pill";
import { SectionCard } from "../components/SectionCard";
import { ResultSummary } from "../components/interview/ResultSummary";
import { RunHistoryList } from "../components/interview/RunHistoryList";
import {
  api,
  buildInterviewSocketUrl,
  type EvaluationCompleteMessage,
  type InterviewSocketMessage,
  type OrchestrationRun,
  type Question,
} from "../lib/api";

type SocketState = "connecting" | "open" | "closed" | "error";

export function InterviewPage() {
  const [searchParams] = useSearchParams();
  const [sessionInput, setSessionInput] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [moduleInput, setModuleInput] = useState(searchParams.get("module") || "");
  const [includeReport, setIncludeReport] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState("");
  const [eventLog, setEventLog] = useState<string[]>([]);
  const [lastResult, setLastResult] = useState<EvaluationCompleteMessage | null>(null);
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const [runs, setRuns] = useState<OrchestrationRun[]>([]);
  const [socketState, setSocketState] = useState<SocketState>("connecting");
  const [transportError, setTransportError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [isPending, startTransition] = useTransition();
  const socketRef = useRef<WebSocket | null>(null);

  function appendLog(line: string) {
    const stamp = new Date().toLocaleTimeString("zh-CN", {
      hour12: false,
    });
    startTransition(() => {
      setEventLog((previous) => [...previous, `[${stamp}] ${line}`]);
    });
  }

  async function refreshRuns(questionId?: string) {
    try {
      const body = await api.orchestrationRuns({
        sessionId: sessionInput.trim() || sessionId || undefined,
        questionId: questionId || currentQuestion?.question_id,
        limit: 20,
      });
      startTransition(() => {
        setRuns(body.runs);
      });
    } catch (error) {
      appendLog(
        `刷新闭环历史失败：${
          error instanceof Error ? error.message : "未知错误"
        }`,
      );
    }
  }

  async function createSession() {
    const created = await api.createSession("interviewer");
    setSessionId(created.session_id);
    setSessionInput(created.session_id);
    appendLog(`新建会话：${created.session_id}`);
    await refreshRuns();
    return created.session_id;
  }

  async function loadQuestion(questionId?: string) {
    const question = questionId
      ? await api.getQuestionById(questionId)
      : await api.randomQuestion(moduleInput.trim() || undefined);
    startTransition(() => {
      setCurrentQuestion(question);
      setLastResult(null);
      setProgressMessages([]);
      setAnswer("");
    });
    appendLog(`已载入题目：${question.question_id}`);
    await refreshRuns(question.question_id);
    return question;
  }

  function connectSocket() {
    if (socketRef.current) {
      socketRef.current.close();
    }

    setSocketState("connecting");
    setTransportError(null);

    const socket = new WebSocket(buildInterviewSocketUrl());
    socketRef.current = socket;

    socket.onopen = () => {
      setSocketState("open");
      appendLog("WebSocket 已连接");
    };

    socket.onclose = () => {
      setSocketState("closed");
      appendLog("WebSocket 已断开");
    };

    socket.onerror = () => {
      setSocketState("error");
      setTransportError("WebSocket 连接出现错误。");
      appendLog("WebSocket 错误");
    };

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as InterviewSocketMessage;
      if (payload.type === "connection_open") {
        appendLog("服务端连接成功");
        return;
      }
      if (payload.type === "evaluation_chunk") {
        appendLog(`进度：${payload.content}`);
        setProgressMessages((previous) => [...previous, payload.content]);
        return;
      }
      if (payload.type === "error") {
        setIsBusy(false);
        setProgressMessages([]);
        appendLog(`错误：${payload.message}`);
        setTransportError(payload.message);
        return;
      }
      setIsBusy(false);
      setProgressMessages([]);
      setLastResult(payload);
      appendLog(payload.message || "评分完成");
      void refreshRuns(payload.question_id);
    };
  }

  async function submitAnswer() {
    if (!currentQuestion?.question_id) {
      appendLog("请先抽取题目");
      return;
    }
    if (!answer.trim()) {
      appendLog("请先输入答案");
      return;
    }
    if (!socketRef.current || socketState !== "open") {
      appendLog("WebSocket 未连接，请先重连");
      return;
    }

    let safeSessionId = sessionInput.trim() || sessionId;
    if (!safeSessionId) {
      safeSessionId = await createSession();
    }

    setIsBusy(true);
    setLastResult(null);
    setProgressMessages(["已提交答案，等待服务端返回..."]);
    socketRef.current.send(
      JSON.stringify({
        type: "submit_answer",
        question_id: currentQuestion.question_id,
        answer,
        session_id: safeSessionId,
        include_report: includeReport,
      }),
    );
    appendLog(`已提交答案：${currentQuestion.question_id}`);
  }

  function clearLog() {
    setEventLog([]);
    setLastResult(null);
    setProgressMessages([]);
    setRuns([]);
  }

  useEffect(() => {
    connectSocket();
    return () => {
      socketRef.current?.close();
    };
  }, []);

  useEffect(() => {
    setModuleInput(searchParams.get("module") || "");
    const questionId = searchParams.get("question_id");
    if (!questionId) {
      return;
    }
    void loadQuestion(questionId);
  }, [searchParams]);

  return (
    <div className="page-grid">
      <SectionCard
        eyebrow="Realtime Interview"
        title="把会话、题目、答题和闭环反馈放在同一个工作台里"
        description="这里不再是最小联调页，而是一个真正的面试工作面板。"
        tone="ink"
        action={
          <div className="button-row">
            <button type="button" className="button button--primary" onClick={() => void createSession()}>
              新建会话
            </button>
            <button type="button" className="button button--ghost" onClick={() => void loadQuestion()}>
              抽取题目
            </button>
            <button type="button" className="button button--ghost" onClick={() => void refreshRuns()}>
              {isPending ? "刷新中..." : "刷新闭环历史"}
            </button>
            <button type="button" className="button button--ghost" onClick={() => connectSocket()}>
              重连 WS
            </button>
          </div>
        }
      >
        <div className="field-grid">
          <label className="field">
            <span>会话 ID</span>
            <input
              value={sessionInput}
              placeholder="留空时自动创建"
              onChange={(event) => setSessionInput(event.target.value)}
            />
          </label>
          <label className="field">
            <span>模块（可选）</span>
            <input
              value={moduleInput}
              placeholder="如 Java基础"
              onChange={(event) => setModuleInput(event.target.value)}
            />
          </label>
        </div>

        <div className="status-strip">
          <Pill
            tone={
              socketState === "open"
                ? "ok"
                : socketState === "error"
                  ? "bad"
                  : "warn"
            }
          >
            WS: {socketState}
          </Pill>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={includeReport}
              onChange={(event) => setIncludeReport(event.target.checked)}
            />
            返回周报摘要
          </label>
          {transportError ? <Pill tone="bad">{transportError}</Pill> : null}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Question"
        title="当前题目"
        description="支持从复习页带 question_id 跳转自动加载。"
      >
        {currentQuestion ? (
          <div className="question-panel">
            <div className="question-panel__title">
              <Pill>{currentQuestion.module || "未知模块"}</Pill>
              <strong>{currentQuestion.title || currentQuestion.question_id}</strong>
            </div>
            <div className="question-panel__meta">
              question_id={currentQuestion.question_id}
            </div>
            <label className="field">
              <span>回答内容</span>
              <textarea
                value={answer}
                placeholder="在这里作答，提交后会触发评分与闭环编排。"
                onChange={(event) => setAnswer(event.target.value)}
              />
            </label>
            <div className="button-row">
              <button
                type="button"
                className="button button--primary"
                disabled={isBusy || socketState !== "open"}
                onClick={() => void submitAnswer()}
              >
                {isBusy ? "提交中..." : "提交答案"}
              </button>
              <button type="button" className="button button--ghost" onClick={() => clearLog()}>
                清空日志
              </button>
            </div>
          </div>
        ) : (
          <EmptyState
            title="还没有载入题目"
            description="可以直接抽题，或从复习页带 question_id 跳进来。"
          />
        )}
      </SectionCard>

      <SectionCard
        eyebrow="Live Feed"
        title="会话消息"
        description="实时显示 WebSocket 状态、评估阶段和错误信息。"
      >
        {eventLog.length ? (
          <pre className="console-panel">{eventLog.join("\n")}</pre>
        ) : (
          <EmptyState
            title="日志面板为空"
            description="建立连接或执行一次提交后，这里会开始出现消息流。"
          />
        )}
      </SectionCard>

      <SectionCard
        eyebrow="Result"
        title="本次闭环结果"
        description="提炼出四维评分、弱点和编排摘要，而不是把所有 JSON 原样甩给用户。"
        tone="signal"
      >
        <ResultSummary result={lastResult} progressMessages={progressMessages} />
      </SectionCard>

      <SectionCard
        eyebrow="History"
        title="历史闭环"
        description="按会话与题目查看已经产生过的编排记录。"
      >
        <RunHistoryList runs={runs} />
      </SectionCard>
    </div>
  );
}
