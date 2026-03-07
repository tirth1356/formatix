import { motion } from "framer-motion";
import { Send, FileText, Check } from "lucide-react";

import { useState } from "react";

const FormattingAgent = () => {
  const [remarks, setRemarks] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (remarks.trim()) {
      setIsSubmitted(true);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-panel p-10 shadow-2xl mb-16 relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -mr-32 -mt-32" />
      
      <div className="flex items-center gap-4 mb-8 relative z-10">
        <div className="h-12 w-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shadow-lg">
          <FileText className="h-6 w-6" />
        </div>
        <div>
            <h2 className="text-2xl font-black text-foreground tracking-tight">Manuscript Remarks</h2>
            <p className="text-sm text-muted-foreground/60 font-medium">Add special formatting instructions for the AI agents</p>
        </div>
      </div>

      <div className="max-w-2xl relative z-10">
        <form onSubmit={handleSubmit} className="relative group">
          <input
            type="text"
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            disabled={isSubmitted}
            placeholder={isSubmitted ? "" : "e.g. 'Ensure all chemical formulas are subscripted' or 'Use British English'"}
            className={`w-full bg-background/50 border-2 rounded-2xl px-8 h-20 text-foreground text-lg placeholder:text-muted-foreground/30 focus:outline-none transition-all pr-20 shadow-inner block backdrop-blur-md ${
              isSubmitted ? "border-green-500/50 cursor-default" : "border-white/5 focus:border-primary/40"
            }`}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSubmit();
              }
            }}
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-3">
            {isSubmitted && (
              <motion.span 
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-green-500 font-black text-sm uppercase tracking-widest mr-2 flex items-center gap-2"
              >
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                Remarks Taken
              </motion.span>
            )}
            <button 
              type="submit"
              disabled={isSubmitted || !remarks.trim()}
              className={`h-14 w-14 rounded-xl flex items-center justify-center transition-all shadow-xl hover:scale-105 active:scale-95 ${
                isSubmitted 
                  ? "bg-green-500 text-white" 
                  : "bg-primary text-primary-foreground hover:bg-primary/90 group-hover:shadow-primary/20"
              } disabled:opacity-50 disabled:hover:scale-100`}
            >
              {isSubmitted ? <Check className="h-6 w-6" /> : <Send className="h-6 w-6" />}
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
};

export default FormattingAgent;
