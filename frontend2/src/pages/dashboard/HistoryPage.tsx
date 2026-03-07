import { motion } from "framer-motion";
import { FileText, Clock, CheckCircle2 } from "lucide-react";

const history = [
  { name: "Neural_Networks_Review.docx", format: "APA 7th", score: 94, date: "2026-03-06 14:32", agents: 6 },
  { name: "Climate_Study_2024.pdf", format: "IEEE", score: 91, date: "2026-03-05 09:15", agents: 6 },
  { name: "Genomics_Paper.docx", format: "Vancouver", score: 88, date: "2026-03-04 16:42", agents: 6 },
  { name: "AI_Ethics_Manuscript.txt", format: "MLA 9th", score: 94, date: "2026-03-03 11:20", agents: 6 },
  { name: "Quantum_Computing.docx", format: "APA 7th", score: 97, date: "2026-03-02 08:55", agents: 6 },
  { name: "Bioinformatics_Study.pdf", format: "Chicago 17th", score: 90, date: "2026-03-01 13:10", agents: 6 },
];

const HistoryPage = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Processing History</h1>
        <p className="text-sm text-muted-foreground">{history.length} manuscripts processed</p>
      </div>

      <div className="space-y-3">
        {history.map((doc, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="glass-panel p-5 flex items-center justify-between hover:border-primary/20 transition-colors cursor-pointer">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{doc.name}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-muted-foreground">{doc.format}</span>
                  <span className="text-xs text-muted-foreground flex items-center gap-1"><Clock className="h-3 w-3" /> {doc.date}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-lg font-bold font-mono ${doc.score >= 90 ? "text-primary" : "text-neon-orange"}`}>{doc.score}%</span>
              <CheckCircle2 className="h-5 w-5 text-primary" />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default HistoryPage;
