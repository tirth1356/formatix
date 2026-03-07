import { createContext, useContext, useState, ReactNode, useCallback } from "react";

export type WorkflowStage = "upload" | "processing" | "results" | "complete";

interface WorkflowContextType {
  stage: WorkflowStage;
  isProcessed: boolean;
  isAuthenticated: boolean;
  userName: string;
  /** Card title selected on UploadPage e.g. "APA 7th Edition" */
  selectedStyle: string;
  setSelectedStyle: (style: string) => void;
  /** Backend job_id from /upload-manuscript, stored after successful upload */
  jobId: string | null;
  setJobId: (id: string) => void;
  /** Whether the user selected Online/Cloud mode instead of Local mode on the upload page */
  isCloudMode: boolean;
  setIsCloudMode: (isCloud: boolean) => void;
  advanceTo: (stage: WorkflowStage) => void;
  login: (name: string) => void;
  logout: () => void;
  resetWorkflow: () => void;
}

const WorkflowContext = createContext<WorkflowContextType | null>(null);

export function WorkflowProvider({ children }: { children: ReactNode }) {
  const [stage, setStage] = useState<WorkflowStage>(() => {
    return (localStorage.getItem("workflow_stage") as WorkflowStage) || "upload";
  });
  const [isProcessed, setIsProcessed] = useState(() => {
    return localStorage.getItem("is_processed") === "true";
  });
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem("is_authenticated") === "true";
  });
  const [selectedStyle, setSelectedStyleState] = useState(() => {
    return localStorage.getItem("selected_style") || "APA 7th Edition";
  });
  const [jobId, setJobIdState] = useState<string | null>(() => {
    return localStorage.getItem("current_job_id");
  });
  const [isCloudMode, setIsCloudModeState] = useState<boolean>(() => {
    return localStorage.getItem("is_cloud_mode") === "true";
  });
  const [userName, setUserName] = useState(() => {
    return localStorage.getItem("user_name") || "";
  });

  const setSelectedStyle = useCallback((style: string) => {
    setSelectedStyleState(style);
    localStorage.setItem("selected_style", style);
  }, []);

  const setJobId = useCallback((id: string) => {
    setJobIdState(id);
    localStorage.setItem("current_job_id", id);
  }, []);

  const setIsCloudMode = useCallback((isCloud: boolean) => {
    setIsCloudModeState(isCloud);
    localStorage.setItem("is_cloud_mode", isCloud ? "true" : "false");
  }, []);

  const stageOrder: WorkflowStage[] = ["upload", "processing", "results", "complete"];

  const advanceTo = useCallback((newStage: WorkflowStage) => {
    setStage((prev) => {
      const currentIdx = stageOrder.indexOf(prev);
      const newIdx = stageOrder.indexOf(newStage);
      const final = newIdx > currentIdx ? newStage : prev;
      localStorage.setItem("workflow_stage", final);

      if (final === "complete" || final === "results") {
        setIsProcessed(true);
        localStorage.setItem("is_processed", "true");
      }

      return final;
    });
  }, []);

  const login = useCallback((name: string) => {
    setIsAuthenticated(true);
    setUserName(name);
    localStorage.setItem("is_authenticated", "true");
    localStorage.setItem("user_name", name);
  }, []);

  const logout = useCallback(() => {
    setIsAuthenticated(false);
    setUserName("");
    setStage("upload");
    setIsProcessed(false);
    localStorage.removeItem("is_authenticated");
    localStorage.removeItem("user_name");
    localStorage.setItem("workflow_stage", "upload");
    localStorage.removeItem("is_processed");
  }, []);

  const resetWorkflow = useCallback(() => {
    setStage("upload");
    setIsProcessed(false);
    setJobIdState(null);
    localStorage.setItem("workflow_stage", "upload");
    localStorage.removeItem("is_processed");
    localStorage.removeItem("current_job_id");
    // Keep selectedStyle and isCloudMode so user's preference persists
  }, []);

  return (
    <WorkflowContext.Provider
      value={{
        stage,
        isProcessed,
        isAuthenticated,
        userName,
        selectedStyle,
        setSelectedStyle,
        jobId,
        setJobId,
        isCloudMode,
        setIsCloudMode,
        advanceTo,
        login,
        logout,
        resetWorkflow,
      }}
    >
      {children}
    </WorkflowContext.Provider>
  );
}

export function useWorkflow() {
  const ctx = useContext(WorkflowContext);
  if (!ctx) throw new Error("useWorkflow must be used within WorkflowProvider");
  return ctx;
}
