import { Navigate, Route, Routes } from "react-router";

import { AppShell } from "../components/AppShell";
import { DashboardPage } from "../routes/DashboardPage";
import { InterviewPage } from "../routes/InterviewPage";
import { ReviewPage } from "../routes/ReviewPage";
import { StatsPage } from "../routes/StatsPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="interview" element={<InterviewPage />} />
        <Route path="review" element={<ReviewPage />} />
        <Route path="stats" element={<StatsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
