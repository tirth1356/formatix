import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Loader2,
  Type,
  Users,
  FileText,
  Image,
  Table2,
  BarChart3,
  BookOpen,
  Quote,
  List,
} from "lucide-react";
import { useWorkflow } from "@/contexts/WorkflowContext";
import { apiGetJob } from "@/lib/api";

const ElementsPage = () => {
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

  const structure = jobData?.formatted_structure || jobData?.structure || {};
  const title = structure.title || "—";
  const authors = structure.authors || [];
  const abstract = structure.abstract || "";
  const keywords = structure.keywords || [];
  const sections = structure.sections || [];
  const tables = structure.tables || [];
  const figures = structure.figures || [];
  const references = structure.references || [];

  const introSection = sections.find(
    (s: any) =>
      /introduction|intro/i.test(String(s.heading || "")) ||
      (/^I\.?\s/i.test(String(s.heading || "")) && sections.indexOf(s) === 0)
  );
  const otherSections = sections.filter(
    (s: any) =>
      s.heading &&
      s.heading !== "[Table]" &&
      s.heading !== "[Figure]" &&
      !/abstract|references?|bibliography|works cited/i.test(String(s.heading))
  );

  const boxClass =
    "rounded-2xl border border-white/10 bg-background/60 backdrop-blur-sm p-5 hover:border-primary/20 transition-colors min-w-0 overflow-hidden";

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-20">
      <div>
        <h1 className="text-3xl font-black text-foreground tracking-tight">Elements</h1>
        <p className="text-muted-foreground mt-1">
          Important elements extracted from the formatted document
          {selectedStyle && (
            <span className="text-primary font-medium"> · {selectedStyle}</span>
          )}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0 }}
          className={boxClass}
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="h-9 w-9 rounded-xl bg-primary/10 flex items-center justify-center">
              <Type className="h-4 w-4 text-primary" />
            </div>
            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
              Title
            </span>
          </div>
          <p className="text-sm font-bold text-foreground break-words leading-snug">
            {title}
          </p>
        </motion.div>

        {/* Authors */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className={boxClass}
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="h-9 w-9 rounded-xl bg-primary/10 flex items-center justify-center">
              <Users className="h-4 w-4 text-primary" />
            </div>
            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
              Authors
            </span>
          </div>
          <p className="text-sm text-foreground/90 break-words">
            {authors.length > 0 ? authors.join(", ") : "—"}
          </p>
        </motion.div>

        {/* Keywords */}
        {keywords.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={boxClass}
          >
            <div className="flex items-center gap-2 mb-3">
              <div className="h-9 w-9 rounded-xl bg-primary/10 flex items-center justify-center">
                <List className="h-4 w-4 text-primary" />
              </div>
              <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
                Keywords
              </span>
            </div>
            <p className="text-sm text-foreground/90 break-words">
              {keywords.join(", ")}
            </p>
          </motion.div>
        )}
      </div>

      {/* Abstract / Introduction */}
      {(abstract || introSection) && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className={boxClass}
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="h-9 w-9 rounded-xl bg-primary/10 flex items-center justify-center">
              <FileText className="h-4 w-4 text-primary" />
            </div>
            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
              {abstract ? "Abstract" : "Introduction"}
            </span>
          </div>
          <p className="text-sm text-foreground/90 leading-relaxed break-words whitespace-pre-wrap">
            {abstract
              ? (abstract.length > 400 ? abstract.slice(0, 400) + "…" : abstract)
              : introSection?.content
                ? (introSection.content.length > 400
                    ? introSection.content.slice(0, 400) + "…"
                    : introSection.content)
                : "—"}
          </p>
        </motion.div>
      )}

      {/* Main sections (Methodology, Results, etc.) */}
      {otherSections.length > 0 && (
        <div>
          <h2 className="text-xs font-black text-muted-foreground uppercase tracking-widest mb-4 flex items-center gap-2">
            <BookOpen className="h-4 w-4" /> Sections
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {otherSections.slice(0, 8).map((sec: any, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 + i * 0.05 }}
                className={boxClass}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Quote className="h-3.5 w-3.5 text-primary/60" />
                  <span className="text-xs font-bold text-primary">
                    {sec.heading}
                  </span>
                </div>
                <p className="text-sm text-foreground/80 leading-relaxed break-words line-clamp-4">
                  {sec.content
                    ? sec.content.length > 280
                      ? sec.content.slice(0, 280) + "…"
                      : sec.content
                    : "—"}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Figures & Graphs */}
      {figures.length > 0 && (
        <div>
          <h2 className="text-xs font-black text-muted-foreground uppercase tracking-widest mb-4 flex items-center gap-2">
            <Image className="h-4 w-4" /> Figures &amp; Graphs
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {figures.map((fig: string, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.03 }}
                className={boxClass}
              >
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 className="h-3.5 w-3.5 text-primary/60" />
                  <span className="text-[10px] font-bold text-muted-foreground uppercase">
                    Figure {i + 1}
                  </span>
                </div>
                <p className="text-xs text-foreground/80 break-words line-clamp-3">
                  {typeof fig === "string" ? fig : JSON.stringify(fig)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Tables */}
      {tables.length > 0 && (
        <div>
          <h2 className="text-xs font-black text-muted-foreground uppercase tracking-widest mb-4 flex items-center gap-2">
            <Table2 className="h-4 w-4" /> Tables
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {tables.map((tbl: string, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25 + i * 0.03 }}
                className={boxClass}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Table2 className="h-3.5 w-3.5 text-primary/60" />
                  <span className="text-[10px] font-bold text-muted-foreground uppercase">
                    Table {i + 1}
                  </span>
                </div>
                <p className="text-xs text-foreground/80 break-words line-clamp-3 font-mono">
                  {typeof tbl === "string" ? tbl : JSON.stringify(tbl)}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* References count */}
      {references.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className={boxClass}
        >
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="h-4 w-4 text-primary/60" />
            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
              References
            </span>
          </div>
          <p className="text-sm text-foreground/80">
            {references.length} reference{references.length !== 1 ? "s" : ""} in
            the formatted document.
          </p>
        </motion.div>
      )}

      {(!jobData?.structure && !jobData?.formatted_structure) ? (
        <div className="glass-panel p-10 text-center">
          <p className="text-muted-foreground">
            No elements to show yet. Run the pipeline (Upload → Processing →
            Results) to extract title, sections, figures, and tables from your
            document.
          </p>
        </div>
      ) : null}
    </div>
  );
};

export default ElementsPage;
