import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import AgentPipeline, { AgentStep } from "@/components/AgentPipeline";
import { FileText, Network, BookOpen, Paintbrush, Quote, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useWorkflow } from "@/contexts/WorkflowContext";
import { apiExtractRules, apiParse, apiAnalyzeStructure, apiAnalyzeCorrections } from "@/lib/api";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";
void BACKEND_URL; // kept for potential future direct-fetch usage

const ProcessingPage = () => {
  const [agents, setAgents] = useState<AgentStep[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();
  const { advanceTo, isProcessed, selectedStyle, jobId, isCloudMode } = useWorkflow();

  // Build dynamic agents & logs based on the selected style
  const makeAgents = (style: string): AgentStep[] => [
    { name: "Parser Agent", description: "Extracting text & metadata from document", icon: FileText, status: "pending" },
    { name: "Structure Agent", description: "Detecting manuscript sections & hierarchy", icon: Network, status: "pending" },
    { name: "Rule Extraction", description: `Loading ${style} formatting rules`, icon: BookOpen, status: "pending" },
    { name: "Formatting Agent", description: `Proposing language & styling corrections`, icon: Paintbrush, status: "pending" },
  ];

  const makeLogMessages = (style: string): string[] => [
    "Initialising parser agent...",
    "Extracting text and metadata from uploaded document",
    "Detected: references, figures, and tables",
    "Analysing manuscript structure...",
    "Identified: Title, Abstract, Introduction, Methods, Results, Discussion, Conclusion",
    `Loading ${style} formatting rules from citation_styles module...`,
    `Rule set loaded: ${style} formatting rules applied`,
    "Generating suggested formatting and language edits...",
    "Review ready — pausing pipeline for user approval.",
  ];

  useEffect(() => {
    setAgents(makeAgents(selectedStyle));
  }, [selectedStyle]);

  useEffect(() => {
    if (isProcessed) {
      setAgents((prev) => prev.map((a) => ({ ...a, status: "complete" as const })));
      setProgress(100);
      navigate("/dashboard/review");
      setLogs(["Using cached completed results."]);
      return;
    }

    const agentSteps = makeAgents(selectedStyle);
    setAgents(agentSteps);
    let isCancelled = false;

    const runAgents = async () => {
      // If we don't have a real job_id yet, fallback to the old simulated timer-based view (demo mode)
      if (!jobId || jobId === "preview") {
        setLogs(["[Demo Simulation Mode] Upload a file for real backend processing."]);
        // ... fast track simulation ...
        let cur = 0;
        const i = setInterval(() => {
          if (isCancelled) {
            clearInterval(i);
            return;
          }
          if (cur >= agentSteps.length) {
            clearInterval(i);
            setProgress(100);
            setTimeout(() => { if (!isCancelled) navigate("/dashboard/review"); }, 2000);
            return;
          }
          setAgents(p => p.map((a, idx) => idx === cur ? { ...a, status: "complete" } : a));
          setProgress(((cur + 1) / agentSteps.length) * 100);
          cur++;
        }, 1000);
        return;
      }

      const updateAgentStatus = (idx: number, status: "running" | "complete" | "error") => {
        if (!isCancelled) setAgents((prev) => prev.map((a, i) => i === idx ? { ...a, status } : a));
      };
      const addLog = (msg: string) => {
        if (!isCancelled) setLogs(p => [...p, msg]);
      };

      try {
        // 1. Parser
        updateAgentStatus(0, "running");
        addLog("Parsing manuscript text and extracting metadata...");
        setProgress(10);
        await apiParse(jobId, isCloudMode);
        updateAgentStatus(0, "complete");

        // 2. Structure
        updateAgentStatus(1, "running");
        addLog("Detecting manuscript sections and hierarchy...");
        setProgress(25);
        await apiAnalyzeStructure(jobId, isCloudMode);
        updateAgentStatus(1, "complete");

        // 3. Rule Extraction
        updateAgentStatus(2, "running");
        addLog(`Extracting formatting rules for ${selectedStyle}...`);
        setProgress(40);
        await apiExtractRules(jobId, selectedStyle, isCloudMode);
        updateAgentStatus(2, "complete");

        // 4. Formatting Document (Analysis only)
        updateAgentStatus(3, "running");
        addLog(`Analyzing and proposing language/format edits (this may take a moment)...`);
        setProgress(75);
        await apiAnalyzeCorrections(jobId, isCloudMode);
        updateAgentStatus(3, "complete");

        setProgress(100);
        addLog("Analysis complete! Redirecting to Review Room...");

        if (!isCancelled) {
          setTimeout(() => navigate("/dashboard/review"), 2000);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          addLog(`Error during processing: ${(err as Error).message || String(err)}`);
          // Set all currently running agents to error state
          setAgents(prev => prev.map(a => a.status === "running" ? { ...a, status: "error" as const } : a));
        }
      }
    };

    runAgents();

    return () => {
      isCancelled = true;
    };
  }, [navigate, advanceTo, isProcessed, selectedStyle, jobId, isCloudMode]);

  return (
    <div className="max-w-5xl mx-auto space-y-10 pb-16">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-black text-foreground tracking-tight">AI Pipeline Active</h1>
        <p className="text-lg text-muted-foreground/60 font-medium">Our agents are meticulously formatting your manuscript.</p>
      </div>

      <div className="glass-panel p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-50" />
        <div className="relative z-10 flex items-center justify-between mb-4">
          <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Total Progress</span>
          <span className="text-lg font-black text-primary drop-shadow-sm">{Math.round(progress)}%</span>
        </div>
        <Progress value={progress} className="h-3 rounded-full bg-foreground/5" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <h3 className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em] px-2">Agent Clusters</h3>
          <div className="glass-panel p-6 shadow-xl">
            <AgentPipeline agents={agents} />
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em] px-2">Live Processing Log</h3>
          <div className="glass-panel p-8 shadow-xl h-[480px] overflow-y-auto scrollbar-thin font-mono text-[13px] leading-relaxed relative bg-background/20">
            <div className="space-y-2">
              {logs.map((log, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="flex gap-3">
                  <span className="text-primary font-bold opacity-50">›</span>
                  <span className="text-foreground/80">{log}</span>
                </motion.div>
              ))}
            </div>
            {logs.length > 0 && (
              <motion.span animate={{ opacity: [1, 0.2] }} transition={{ repeat: Infinity, duration: 1 }} className="text-primary inline-block ml-6 mt-1 shadow-glow font-black">
                _
              </motion.span>
            )}
          </div>
          {progress === 100 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-6 flex justify-center">
              <Button
                onClick={() => navigate("/dashboard/review")}
                size="lg"
                className="w-full h-16 bg-primary text-primary-foreground hover:bg-primary/90 rounded-2xl text-xl font-black shadow-2xl transition-all hover:scale-[1.03] active:scale-[0.97]"
              >
                Enter Review Suite
              </Button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProcessingPage;
