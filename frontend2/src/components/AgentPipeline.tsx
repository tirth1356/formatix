import { motion } from "framer-motion";
import { FileText, Network, BookOpen, Paintbrush, ShieldCheck, Quote, Check, Loader2 } from "lucide-react";

export type AgentStatus = "pending" | "running" | "complete" | "error";

export interface AgentStep {
  name: string;
  description: string;
  icon: React.ElementType;
  status: AgentStatus;
}

const defaultAgents: AgentStep[] = [
  { name: "Parser Agent", description: "Extracting text & metadata", icon: FileText, status: "pending" },
  { name: "Structure Agent", description: "Detecting manuscript structure", icon: Network, status: "pending" },
  { name: "Rule Extraction", description: "Loading formatting rules", icon: BookOpen, status: "pending" },
  { name: "Formatting Agent", description: "Applying journal style", icon: Paintbrush, status: "pending" },
  { name: "Citation Engine", description: "Verifying references", icon: Quote, status: "pending" },
  { name: "Validation Agent", description: "Compliance check", icon: ShieldCheck, status: "pending" },
];

interface AgentPipelineProps {
  agents?: AgentStep[];
}

const statusColors: Record<AgentStatus, string> = {
  pending: "border-muted-foreground/30",
  running: "border-neon-green neon-glow-green",
  complete: "border-neon-green",
  error: "border-destructive",
};

const AgentPipeline = ({ agents = defaultAgents }: AgentPipelineProps) => {
  return (
    <div className="space-y-3">
      {agents.map((agent, i) => (
        <motion.div
          key={agent.name}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.1 }}
          className={`glass-panel p-4 flex items-center gap-4 border ${statusColors[agent.status]} transition-all duration-500`}
        >
          <div className={`p-2 rounded-lg ${agent.status === "complete" ? "bg-primary/20" : agent.status === "running" ? "bg-primary/10" : "bg-muted"}`}>
            <agent.icon className={`h-5 w-5 ${agent.status === "complete" ? "text-primary" : agent.status === "running" ? "text-primary animate-pulse" : "text-muted-foreground"}`} />
          </div>
          <div className="flex-1">
            <p className={`font-medium text-sm ${agent.status === "complete" ? "text-primary" : agent.status === "running" ? "text-foreground" : "text-muted-foreground"}`}>
              {agent.name}
            </p>
            <p className="text-xs text-muted-foreground">{agent.description}</p>
          </div>
          <div>
            {agent.status === "complete" && <Check className="h-5 w-5 text-primary" />}
            {agent.status === "running" && <Loader2 className="h-5 w-5 text-primary animate-spin" />}
            {agent.status === "pending" && <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />}
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default AgentPipeline;
