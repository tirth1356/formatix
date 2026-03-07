import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Filter, Loader2 } from "lucide-react";
import { useWorkflow } from "@/contexts/WorkflowContext";
import { apiGetJob } from "@/lib/api";

const fakeCorrections = [
  { type: "heading", before: 'abstract', after: 'Abstract', rule: "APA Level 1: Centered, Bold, Title Case", category: "Headings" },
  { type: "heading", before: 'introduction', after: 'Introduction', rule: "APA Level 1 heading format", category: "Headings" },
  { type: "citation", before: '(Smith 2024)', after: '(Smith, 2024)', rule: "APA: comma between author and year", category: "Citations" },
  { type: "citation", before: '(Smith, 2024, p.12)', after: '(Smith, 2024, p. 12)', rule: "APA: space after 'p.'", category: "Citations" },
  { type: "format", before: 'Arial 11pt', after: 'Times New Roman 12pt', rule: "APA 7th standard body font", category: "Formatting" },
  { type: "format", before: 'Spacing: 1.5', after: 'Spacing: 2.0 (double)', rule: "APA requires double spacing", category: "Formatting" },
  { type: "reference", before: 'Fig 1:', after: 'Figure 1.', rule: "Spell out 'Figure', end with period", category: "Figures" },
  { type: "reference", before: 'et. al.', after: 'et al.', rule: "No period after 'et'", category: "Citations" },
  { type: "format", before: 'Margin: 1 inch left, 0.5 right', after: 'Margin: 1 inch all sides', rule: "APA uniform 1-inch margins", category: "Formatting" },
  { type: "heading", before: 'RESULTS AND DISCUSSION', after: 'Results and Discussion', rule: "APA Level 1: Title Case, not ALL CAPS", category: "Headings" },
];

const categories = ["All", "Headings", "Citations", "Formatting", "Figures"];

const CorrectionsPage = () => {
  const { jobId, selectedStyle } = useWorkflow();
  const [jobData, setJobData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("All");

  useEffect(() => {
    if (!jobId || jobId === "preview") {
      setLoading(false);
      return;
    }

    const loadJob = async () => {
      try {
        const data = await apiGetJob(jobId);
        setJobData(data);
      } catch (err) {
        console.error("Failed to fetch job data", err);
      } finally {
        setLoading(false);
      }
    };
    loadJob();
  }, [jobId]);

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
      </div>
    );
  }

  const allCorrections = Array.isArray(jobData?.corrections) && jobData.corrections.length > 0 
    ? jobData.corrections.map((c: any) => ({
        type: c.type || "format",
        before: c.original || "Unknown",
        after: c.change || "Corrected",
        rule: c.reason || `Matched ${selectedStyle} template`,
        category: c.type === "citation" ? "Citations" 
                : c.type === "heading" ? "Headings" 
                : "Formatting"
      }))
    : fakeCorrections;

  const filtered = filter === "All" ? allCorrections : allCorrections.filter((c: any) => c.category === filter);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">All Corrections</h1>
        <p className="text-sm text-muted-foreground">{allCorrections.length} changes applied with explanations</p>
      </div>

      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        {categories.map((c) => (
          <button key={c} onClick={() => setFilter(c)} className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${filter === c ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:border-primary/30"}`}>
            {c}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {filtered.map((c, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} className="glass-panel p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-accent/20 text-accent">{c.category}</span>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-2">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Before</p>
                <p className="text-sm font-mono text-destructive line-through">{c.before}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">After</p>
                <p className="text-sm font-mono text-primary">{c.after}</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground pt-2 border-t border-border">{c.rule}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default CorrectionsPage;
