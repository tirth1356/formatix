import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Upload, Zap, Shield, FileText, ArrowRight, Brain, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  { icon: Brain, title: "6 AI Agents", desc: "Parser, Structure, Rules, Formatting, Citation, Validation" },
  { icon: Shield, title: "Privacy First", desc: "Local LLM processing with Ollama — your data never leaves" },
  { icon: FileText, title: "Multi-Format", desc: "APA, MLA, Chicago, IEEE, Vancouver + custom templates" },
  { icon: Eye, title: "Explainable AI", desc: "Every change comes with a clear, human-readable reason" },
];

const formats = ["APA 7th", "MLA 9th", "Chicago 17th", "IEEE", "Vancouver", "Custom"];

import { ThemeToggle } from "@/components/ThemeToggle";
import { useWorkflow } from "@/contexts/WorkflowContext";

const Landing = () => {
  const navigate = useNavigate();
  const { resetWorkflow } = useWorkflow();

  const handleGetStarted = () => {
    resetWorkflow();
    navigate("/dashboard/upload");
  };

  const handleDashboard = () => {
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden bg-grid-pattern">
      {/* Ambient light */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/20 rounded-full blur-[150px] opacity-20" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[300px] bg-accent/20 rounded-full blur-[120px] opacity-10" />
      </div>

      {/* Nav */}
      <nav className="relative z-20 flex items-center justify-between px-8 py-5 border-b border-white/5 bg-background/40 backdrop-blur-md sticky top-0">
        <div className="flex items-center gap-2.5">
          <div className="h-10 w-10 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-lg">
            <Zap className="h-5 w-5 text-primary" />
          </div>
          <span className="font-bold text-xl text-foreground tracking-tighter">FormatIX</span>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-2xl px-6 h-10 font-bold shadow-xl transition-all hover:scale-[1.05]" onClick={handleGetStarted}>
            Get Started
          </Button>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 flex flex-col items-center justify-center pt-28 pb-20 px-4">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="text-center max-w-3xl">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-sm mb-8">
            <Zap className="h-3.5 w-3.5" /> Next Gen Document Formatter
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.1] mb-6">
            <span className="text-foreground">AI Powered</span>
            <br />
            <span className="text-gradient-primary">Manuscript Formatting</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto mb-10 leading-relaxed">
            Convert research papers into journal-ready manuscripts in seconds. Six AI agents parse, format, validate, and explain every change.
          </p>
          <div className="flex flex-col sm:flex-row items-center gap-3 justify-center">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 gap-2 px-8 h-12 text-base rounded-xl shadow-[0_4px_24px_-8px_hsl(var(--primary)/0.4)]" onClick={handleGetStarted}>
              <Upload className="h-5 w-5" /> Upload Manuscript
            </Button>
            <Button size="lg" variant="outline" className="border-border/60 text-foreground hover:bg-muted/50 gap-2 px-8 h-12 text-base rounded-xl" onClick={handleDashboard}>
              Try Demo <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </motion.div>

        {/* Format badges */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="flex flex-wrap items-center justify-center gap-2 mt-14">
          {formats.map((f) => (
            <span key={f} className="px-3 py-1 text-xs rounded-lg bg-muted/50 border border-border/40 text-muted-foreground">
              {f}
            </span>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section className="relative z-10 max-w-5xl mx-auto px-4 pb-28 pt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.08 }}
              className="bg-card/50 backdrop-blur-lg border border-border/40 rounded-2xl p-6 hover:border-primary/20 transition-all duration-300 group"
            >
              <div className="h-10 w-10 rounded-xl bg-primary/8 flex items-center justify-center mb-4 group-hover:bg-primary/15 transition-colors">
                <f.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground mb-1">{f.title}</h3>
              <p className="text-sm text-muted-foreground/80">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 bg-background/40 backdrop-blur-xl pt-20 pb-10 px-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          <div className="col-span-1 md:col-span-1 space-y-6">
            <div className="flex items-center gap-2.5">
              <div className="h-10 w-10 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-lg">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <span className="font-bold text-xl text-foreground tracking-tighter uppercase whitespace-nowrap">FormatIX</span>
            </div>
            <p className="text-sm text-muted-foreground/60 leading-relaxed font-medium">
              Revolutionizing academic formatting with multi-agent AI clusters. Built for researchers, by researchers.
            </p>
          </div>
          
          <div className="space-y-6">
            <h4 className="text-xs font-black text-muted-foreground uppercase tracking-[0.3em]">Foundation</h4>
            <ul className="space-y-4">
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">Architecture</a></li>
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">AI Protocols</a></li>
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">Security Matrix</a></li>
            </ul>
          </div>

          <div className="space-y-6">
            <h4 className="text-xs font-black text-muted-foreground uppercase tracking-[0.3em]">Ecosystem</h4>
            <ul className="space-y-4">
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">Journal Templates</a></li>
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">API Documentation</a></li>
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">Cloud Inference</a></li>
            </ul>
          </div>

          <div className="space-y-6">
            <h4 className="text-xs font-black text-muted-foreground uppercase tracking-[0.3em]">Network</h4>
            <ul className="space-y-4">
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">Community</a></li>
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">Research Hub</a></li>
              <li><a href="#" className="text-sm text-muted-foreground/60 hover:text-primary transition-colors font-medium">Support</a></li>
            </ul>
          </div>
        </div>
        
        <div className="max-w-7xl mx-auto pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-6">
          <p className="text-[11px] font-bold text-muted-foreground/40 uppercase tracking-widest">
            © 2026 FormatIX · All systems operational
          </p>
          <div className="flex items-center gap-6">
            <span className="text-[10px] font-black text-primary/40 uppercase tracking-widest cursor-pointer hover:text-primary transition-colors">Privacy Protocal</span>
            <span className="text-[10px] font-black text-primary/40 uppercase tracking-widest cursor-pointer hover:text-primary transition-colors">Service Level Agreement</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
