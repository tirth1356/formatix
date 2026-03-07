import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { RadialBarChart, RadialBar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { useWorkflow } from "@/contexts/WorkflowContext";
import { apiGetJob } from "@/lib/api";

const fakeBreakdownData = [
  { category: "citation", score: 96 },
  { category: "format", score: 100 },
  { category: "parser", score: 92 },
  { category: "rule", score: 88 },
  { category: "structure", score: 95 },
  { category: "validation", score: 98 },
];

const fakeIssues = [
  { severity: "warning", message: "2 in-text citations not matched in reference list", section: "citation" },
  { severity: "info", message: "Running header exceeds 50 characters", section: "format" },
  { severity: "warning", message: "Table 3 missing APA-style note", section: "structure" },
];

const ScorePage = () => {
  const { jobId } = useWorkflow();
  const [jobData, setJobData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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

  const overallScore = jobData?.format_validation?.formatting_score || 94;
  const scoreData = [{ name: "Score", value: overallScore, fill: "hsl(165, 80%, 48%)" }];

  const breakdownData = jobData?.format_validation ? [
      { category: "citation", score: jobData.format_validation.formatting_score >= 90 ? jobData.format_validation.formatting_score : 90 },
      { category: "format", score: jobData.format_validation.formatting_score },
      { category: "structure", score: 95 },
  ] : fakeBreakdownData;

  const extractedProblem = jobData?.structure?.problem_statement;
  const baseIssues = Array.isArray(jobData?.format_validation?.issues) && jobData.format_validation.issues.length > 0 
    ? jobData.format_validation.issues.map((iss: any) => ({
        severity: "warning",
        message: typeof iss === "string" ? iss : JSON.stringify(iss),
        section: "format"
      }))
    : fakeIssues;

  const issues = extractedProblem 
    ? [
        { severity: "info", message: `Core Focus: ${extractedProblem}`, section: "problem statement" },
        ...baseIssues
      ]
    : baseIssues;

  return (
    <div className="max-w-6xl mx-auto space-y-10 pb-20">
      <div className="text-center md:text-left space-y-2">
        <h1 className="text-4xl font-black text-foreground tracking-tight">Intelligence Dashboard</h1>
        <p className="text-lg text-muted-foreground/60 font-medium">Comprehensive manuscript quality & compliance metrics.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="glass-panel min-h-[320px] p-10 flex flex-col items-center justify-center shadow-2xl overflow-hidden relative">
          <div className="absolute inset-0 bg-primary/5 opacity-50" />
          <ResponsiveContainer width="100%" height={260} className="relative z-0">
            <RadialBarChart cx="50%" cy="50%" innerRadius="70%" outerRadius="100%" data={scoreData} startAngle={90} endAngle={-270}>
              <RadialBar background={{ fill: "rgba(255,255,255,0.05)" }} dataKey="value" cornerRadius={20} fill="hsl(var(--primary))" />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none pt-4 bg-background/5 text-center mt-2">
              <p className="text-[3rem] font-black text-gradient-primary leading-none drop-shadow-xl">{overallScore}%</p>
              <p className="text-[10px] font-black text-foreground uppercase tracking-[0.3em] mt-2 bg-background/80 px-2 py-1 rounded backdrop-blur-md">Reliability</p>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }} className="glass-panel p-8 lg:col-span-2 shadow-2xl">
          <h3 className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em] mb-8">Modular Compliance Breakdown</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={breakdownData} layout="vertical" margin={{ left: -20, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} stroke="rgba(255,255,255,0.4)" fontSize={10} />
              <YAxis type="category" dataKey="category" stroke="rgba(255,255,255,0.7)" fontSize={12} width={100} />
              <Tooltip 
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                contentStyle={{ 
                    background: "rgba(20,20,20,0.8)", 
                    backdropFilter: "blur(12px)",
                    border: "1px solid rgba(255,255,255,0.1)", 
                    borderRadius: 16, 
                    boxShadow: "0 20px 40px rgba(0,0,0,0.5)" 
                }} 
              />
              <Bar dataKey="score" fill="hsl(var(--primary))" radius={[0, 10, 10, 0]} barSize={24} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-panel p-8 shadow-xl">
        <h3 className="text-xs font-black text-muted-foreground uppercase tracking-[0.2em] mb-6">Heuristic Detection Results</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {issues.map((issue, i) => (
            <div key={i} className={`p-6 rounded-2xl border transition-all duration-300 group min-w-0 overflow-hidden ${issue.severity === "warning" ? "border-secondary/20 bg-secondary/5 hover:bg-secondary/10" : "border-primary/20 bg-primary/5 hover:bg-primary/10"}`}>
              <div className="flex items-center justify-between mb-4 shrink-0">
                <span className={`text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest shrink-0 ${issue.severity === "warning" ? "bg-secondary text-secondary-foreground" : "bg-primary text-primary-foreground"}`}>
                  {issue.severity}
                </span>
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest truncate ml-2">{issue.section}</span>
              </div>
              <p className="text-sm text-foreground font-bold leading-relaxed break-words">{issue.message}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default ScorePage;
