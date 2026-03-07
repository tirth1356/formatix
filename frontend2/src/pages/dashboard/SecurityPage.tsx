import { motion } from "framer-motion";
import { Shield, Lock, Server, Eye, CheckCircle2 } from "lucide-react";

const checks = [
  { label: "Local Processing", desc: "All manuscripts processed on-device via Ollama", status: true, icon: Server },
  { label: "No Cloud Upload", desc: "Private mode ensures zero data transmission", status: true, icon: Lock },
  { label: "End-to-End Privacy", desc: "Documents never leave your infrastructure", status: true, icon: Shield },
  { label: "Audit Logging", desc: "All agent actions are logged locally", status: true, icon: Eye },
];

const SecurityPage = () => (
  <div className="max-w-3xl mx-auto space-y-6">
    <div>
      <h1 className="text-2xl font-bold text-foreground">Security & Privacy</h1>
      <p className="text-sm text-muted-foreground">Your manuscripts are processed with enterprise-grade privacy</p>
    </div>
    <div className="space-y-3">
      {checks.map((c, i) => (
        <motion.div key={c.label} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }} className="glass-panel p-5 flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center"><c.icon className="h-5 w-5 text-primary" /></div>
          <div className="flex-1">
            <p className="font-medium text-foreground text-sm">{c.label}</p>
            <p className="text-xs text-muted-foreground">{c.desc}</p>
          </div>
          <CheckCircle2 className="h-5 w-5 text-primary" />
        </motion.div>
      ))}
    </div>
  </div>
);

export default SecurityPage;
