import { motion } from "framer-motion";
import { FileText, Network, BookOpen, Paintbrush, Quote, ShieldCheck, Activity, Cpu, Zap } from "lucide-react";

const agents = [
  { name: "Parser Agent", icon: FileText, desc: "Extracts text, metadata, figures and tables from PDF, DOCX, and TXT files", tech: "pdfplumber, python-docx", status: "online", load: "12%" },
  { name: "Structure Agent", icon: Network, desc: "Detects manuscript sections: title, abstract, introduction, methods, results, discussion, conclusion, references", tech: "NLP + Llama 3", status: "online", load: "8%" },
  { name: "Rule Extraction Agent", icon: BookOpen, desc: "Extracts formatting rules for APA, MLA, Chicago, IEEE, Vancouver. Supports custom guideline uploads", tech: "Llama 3 + Rule Engine", status: "online", load: "5%" },
  { name: "Formatting Agent", icon: Paintbrush, desc: "Applies heading hierarchy, font styles, line spacing, margins, reference formatting, figure captions", tech: "python-docx + Rules", status: "online", load: "15%" },
  { name: "Citation Engine", icon: Quote, desc: "Verifies citation integrity, matches in-text citations with references, detects duplicates and missing refs", tech: "Regex + NLP", status: "online", load: "10%" },
  { name: "Validation Agent", icon: ShieldCheck, desc: "Checks formatting compliance, generates score, reports issues with headings, spacing, and citations", tech: "Rule Validator", status: "online", load: "7%" },
];

const AgentsPage = () => {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">AI Agents</h1>
          <p className="text-sm text-muted-foreground">6 autonomous agents powering the pipeline</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20">
          <Activity className="h-4 w-4 text-primary animate-pulse" />
          <span className="text-xs text-primary font-mono">All agents online</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agents.map((agent, i) => (
          <motion.div key={agent.name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }} className="glass-panel p-5 hover:border-primary/20 transition-colors">
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                <agent.icon className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-semibold text-foreground text-sm">{agent.name}</h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-mono">{agent.status}</span>
                </div>
                <p className="text-xs text-muted-foreground mb-3">{agent.desc}</p>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground font-mono">{agent.tech}</span>
                  <span className="text-muted-foreground">Load: <span className="text-primary">{agent.load}</span></span>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default AgentsPage;
