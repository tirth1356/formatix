import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { WorkflowProvider } from "@/contexts/WorkflowContext";
import Landing from "./pages/Landing";
import DashboardLayout from "./components/DashboardLayout";
import UploadPage from "./pages/dashboard/UploadPage";
import ProcessingPage from "./pages/dashboard/ProcessingPage";
import ResultsPage from "./pages/dashboard/ResultsPage";
import ElementsPage from "./pages/dashboard/ElementsPage";
import ComparePage from "./pages/dashboard/ComparePage";
import ScorePage from "./pages/dashboard/ScorePage";
import ReviewPage from "./pages/dashboard/ReviewPage";
import CorrectionsPage from "./pages/dashboard/CorrectionsPage";
import HistoryPage from "./pages/dashboard/HistoryPage";
import AgentsPage from "./pages/dashboard/AgentsPage";
import SecurityPage from "./pages/dashboard/SecurityPage";
import SettingsPage from "./pages/dashboard/SettingsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

import { ThemeProvider } from "@/contexts/ThemeContext";

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <ThemeProvider>
        <WorkflowProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/dashboard" element={<DashboardLayout />}>
                <Route index element={<Navigate to="upload" replace />} />
                <Route path="upload" element={<UploadPage />} />
                <Route path="processing" element={<ProcessingPage />} />
                <Route path="results" element={<ResultsPage />} />
                <Route path="elements" element={<ElementsPage />} />
                <Route path="compare" element={<ComparePage />} />
                <Route path="review" element={<ReviewPage />} />
                <Route path="score" element={<ScorePage />} />
                <Route path="corrections" element={<CorrectionsPage />} />
                <Route path="history" element={<HistoryPage />} />
                <Route path="agents" element={<AgentsPage />} />
                <Route path="security" element={<SecurityPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </WorkflowProvider>
      </ThemeProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
