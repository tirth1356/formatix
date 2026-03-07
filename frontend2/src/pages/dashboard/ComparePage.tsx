import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { useWorkflow } from "@/contexts/WorkflowContext";
import { apiGetJob } from "@/lib/api";

const ComparePage = () => {
  const { jobId, selectedStyle } = useWorkflow();
  const [jobData, setJobData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId || jobId === "preview") {
      setLoading(false);
      return;
    }

    const loadJob = async () => {
      try {
        const data = await apiGetJob(jobId, true); // include parsed for original text
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

  const formatParsedText = (parsed: any) => {
    if (!parsed) return null;
    if (typeof parsed === "string") return parsed;
    if (parsed.text) return parsed.text;
    return null;
  };

  const formatDocumentText = (s: any) => {
    if (!s) return null;
    let content = "";
    if (s.title) content += `${s.title}\n\n`;
    if (s.authors && s.authors.length) content += `${s.authors.join(", ")}\n\n`;
    if (s.abstract) content += `Abstract\n${s.abstract}\n\n`;
    if (s.sections && s.sections.length) {
      s.sections.forEach((sec: any) => {
        if (sec.heading && sec.heading !== "[Table]") content += `${sec.heading}\n`;
        if (sec.content) content += `${sec.content}\n\n`;
      });
    }
    if (s.references && s.references.length) {
      content += `References\n`;
      s.references.forEach((ref: string) => {
        content += `${ref}\n`;
      });
    }
    return content.trim();
  };

  const originalText = formatParsedText(jobData?.parsed);
  const formattedText = formatDocumentText(jobData?.formatted_structure || jobData?.structure) || "Preview unavailable.";
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Before vs After</h1>
        <p className="text-sm text-muted-foreground">Side-by-side comparison of formatting changes</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="h-3 w-3 rounded-full bg-destructive" />
            <h3 className="text-sm font-semibold text-foreground">Original</h3>
          </div>
          <pre className="text-sm text-muted-foreground font-mono whitespace-pre-wrap leading-relaxed break-words">{originalText ?? "Original document text not available. Run Parse first."}</pre>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-sm font-semibold text-foreground">Formatted ({selectedStyle})</h3>
          </div>
          <pre className="text-sm text-primary/90 font-mono whitespace-pre-wrap leading-relaxed">{formattedText}</pre>
        </motion.div>
      </div>
    </div>
  );
};

export default ComparePage;
