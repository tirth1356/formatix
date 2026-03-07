import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, X, File, ArrowRight, Shield, Cloud, Zap, Loader2, FileText, Type } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useWorkflow } from "@/contexts/WorkflowContext";
import FormattingAgent from "@/components/upload/FormattingAgent";
import TemplateCard from "@/components/upload/TemplateCard";
import { apiUploadManuscript, apiUploadText } from "@/lib/api";

const templateOptions = [
  {
    title: "APA 7th Edition",
    description: ["Double spaced", "Author-date citations", "Title page required"],
    previewContent: (
      <div className="space-y-6">
        <div className="text-center font-serif space-y-2 mb-8">
          <p className="text-xs uppercase tracking-widest text-muted-foreground">Title Page</p>
          <h4 className="text-xl font-bold">The Impact of AI on Modern Research</h4>
          <p className="text-sm">John Doe</p>
          <p className="text-sm italic">Department of Information Systems</p>
        </div>
        <div className="space-y-4 font-serif leading-loose text-sm">
          <p>This is a sample of APA 7th edition formatting. Note the double spacing and specific heading styles. APA requires a title page and specific citation formats.</p>
          <p>According to Smith (2023), AI is transforming research methodologies...</p>
        </div>
      </div>
    )
  },
  {
    title: "IEEE Standard",
    description: ["Two-column layout", "Numbered citations", "Abstract required"],
    previewContent: (
      <div className="grid grid-cols-2 gap-8 font-serif text-[10px]">
        <div className="col-span-2 text-center mb-4">
          <h4 className="text-sm font-bold uppercase">Automated Formatting Systems for Academic Journals</h4>
          <p className="italic">Jane Smith, Member, IEEE</p>
        </div>
        <div className="space-y-2">
          <p className="font-bold">Abstract— This paper discusses the implementation of multi-agent AI systems...</p>
          <p>I. INTRODUCTION</p>
          <p>Formatted in two columns as per IEEE standards [1], with numbered references in square brackets.</p>
        </div>
        <div className="space-y-2">
          <p>II. METHODOLOGY</p>
          <p>The system utilizes a hierarchical agent architecture to ensure compliance with strict...</p>
        </div>
      </div>
    )
  },
  {
    title: "Nature Journal",
    description: ["Superscript citations", "Strict word limits", "Methods at end"],
    previewContent: (
      <div className="space-y-4 font-serif text-sm">
        <h4 className="text-lg font-bold leading-tight">High-throughput neural formatting of scientific manuscripts</h4>
        <div className="flex gap-2 text-[10px] text-muted-foreground font-sans">
          <span>ARTICLES</span>
          <span>|</span>
          <span>VOLUME 587</span>
        </div>
        <p className="leading-snug">Scientific communication requires precision. Here we report on a system that leverages large language models to automate the laborious task of journal formatting<sup>1</sup>. Our approach demonstrates 99.8% compliance across 500 test cases<sup>2,3</sup>.</p>
        <div className="h-32 bg-foreground/5 rounded-xl border border-white/5 flex items-center justify-center italic text-xs">
          [Figure 1: Performance metrics of AI Agents]
        </div>
      </div>
    )
  },
  {
    title: "MLA 9th Edition",
    description: ["Author-page citations", "Works cited page", "Specific margins"],
    previewContent: (
      <div className="space-y-4 font-serif text-sm">
        <h4 className="text-lg font-bold leading-tight">MLA 9th Edition Formatting</h4>
        <p>Double-spaced, 1-inch margins, author-page in-text citations (e.g., <i>Smith 45</i>), and a Works Cited page. Common in humanities and language arts.</p>
        <div className="h-20 bg-foreground/5 rounded-xl border border-white/5 flex items-center justify-center italic text-xs">
          [Sample: Works Cited page]
        </div>
      </div>
    )
  },
  {
    title: "Chicago Manual of Style",
    description: ["Footnotes or endnotes", "Bibliography", "Distinctive title page"],
    previewContent: (
      <div className="space-y-4 font-serif text-sm">
        <h4 className="text-lg font-bold leading-tight">Chicago Manual of Style</h4>
        <p>Offers both notes-bibliography (footnotes/endnotes) and author-date citation systems. Distinctive title page, full bibliography, and flexible citation options. Widely used in history and publishing.</p>
        <div className="h-20 bg-foreground/5 rounded-xl border border-white/5 flex items-center justify-center italic text-xs">
          [Sample: Footnote and Bibliography]
        </div>
      </div>
    )
  },
  {
    title: "Custom Template",
    description: ["Define your own rules", "Upload style guidelines", "Flexible formatting"],
    isCustom: true,
    previewContent: (
      <div className="space-y-4 font-serif text-sm">
        <h4 className="text-lg font-bold leading-tight">Custom Template</h4>
        <p>Upload your own style guidelines or manuscript. Flexible formatting for journals, institutions, or unique requirements—define your own structure and rules.</p>
        <div className="h-20 bg-foreground/5 rounded-xl border border-white/5 flex items-center justify-center italic text-xs">
          [Custom formatting preview]
        </div>
      </div>
    )
  },
];

const UploadPage = () => {
  // Tabs: "file" | "text"
  const [activeTab, setActiveTab] = useState<"file" | "text">("file");
  // Raw text content
  const [rawText, setRawText] = useState("");
  // Raw File objects (for actual upload)
  const [rawFiles, setRawFiles] = useState<File[]>([]);
  // Display metadata
  const [files, setFiles] = useState<{ name: string; size: string; type: string }[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { advanceTo, selectedStyle, setSelectedStyle, setJobId, isCloudMode, setIsCloudMode } = useWorkflow();

  const addFiles = (incoming: FileList | File[]) => {
    const arr = Array.from(incoming);
    setRawFiles((prev) => [...prev, ...arr]);
    setFiles((prev) => [
      ...prev,
      ...arr.map((f) => ({
        name: f.name,
        size: `${(f.size / (1024 * 1024)).toFixed(2)} MB`,
        type: f.type,
      })),
    ]);
    setUploadError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(e.target.files);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files) addFiles(e.dataTransfer.files);
  }, []);

  const handleStart = async () => {
    if (activeTab === "file" && rawFiles.length === 0) return;
    if (activeTab === "text" && !rawText.trim()) return;

    setUploading(true);
    setUploadError(null);
    try {
      let job_id;
      if (activeTab === "file") {
        const res = await apiUploadManuscript(rawFiles[0]);
        job_id = res.job_id;
      } else {
        const res = await apiUploadText(rawText);
        job_id = res.job_id;
      }
      setJobId(job_id);
    } catch (err: any) {
      setUploadError(err.message || "Failed to start processing");
      setUploading(false);
      return;
    } finally {
      setUploading(false);
    }
    advanceTo("processing");
    navigate("/dashboard/processing");
  };

  return (
    <div className="max-w-6xl mx-auto space-y-12 pb-20">
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-black text-foreground tracking-tight">Upload Manuscript</h1>
        <p className="text-lg text-muted-foreground/60 font-medium max-w-2xl mx-auto">Deploy our multi-agent AI cluster to transform your research into a polished, journal-ready masterpiece.</p>
      </div>

      {/* How to Use Section */}
      <div className="space-y-8">
        <div className="flex items-center gap-4 px-2">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                <Zap className="h-4 w-4" />
            </div>
            <h2 className="text-xs font-black text-muted-foreground uppercase tracking-[0.3em]">Protocol Execution Guide</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
                { step: "01", title: "Upload", desc: "Drop your manuscript (PDF/DOCX)", icon: Upload },
                { step: "02", title: "Remarks", desc: "Define special formatting rules", icon: File },
                { step: "03", title: "Template", desc: "Select target journal standard", icon: Shield },
                { step: "04", title: "Deploy", desc: "AI agents execute formatting", icon: Cloud },
            ].map((s, i) => (
                <motion.div 
                    key={s.step}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="glass-panel p-6 border-white/5 hover:border-primary/20 transition-all duration-500 group relative overflow-hidden"
                >
                    <div className="absolute top-0 right-0 p-4">
                        <span className="text-4xl font-black text-foreground/5 group-hover:text-primary/10 transition-colors uppercase tracking-tighter">{s.step}</span>
                    </div>
                    <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                        <s.icon className="h-5 w-5" />
                    </div>
                    <h3 className="font-black text-foreground tracking-tight mb-1">{s.title}</h3>
                    <p className="text-xs text-muted-foreground/60 font-medium leading-relaxed">{s.desc}</p>
                </motion.div>
            ))}
        </div>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        multiple
      />

      <div className="flex justify-center mb-6">
        <div className="inline-flex items-center p-1 rounded-2xl bg-white/5 border border-white/5 backdrop-blur-sm">
          <button
            onClick={() => setActiveTab("file")}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-medium transition-all duration-300 ${
              activeTab === "file" ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <File className="h-4 w-4" />
            Upload File
          </button>
          <button
            onClick={() => setActiveTab("text")}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-medium transition-all duration-300 ${
              activeTab === "text" ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Type className="h-4 w-4" />
            Paste Text
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === "file" ? (
          <motion.div
            key="file-drop"
            initial={{ opacity: 0, scale: 0.98, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -10 }}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`glass-panel p-20 text-center cursor-pointer transition-all duration-500 relative overflow-hidden group ${
              dragOver
                ? "border-primary shadow-[0_32px_64px_-12px_rgba(var(--primary),0.2)] scale-[1.02]"
                : "border-white/5 hover:border-primary/20 hover:shadow-2xl shadow-sm"
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative z-10 flex flex-col items-center">
                <div className={`h-20 w-20 rounded-3xl flex items-center justify-center mb-8 transition-all duration-500 group-hover:rotate-6 ${dragOver ? "bg-primary text-primary-foreground shadow-glow" : "bg-primary/10 text-primary border border-primary/20"}`}>
                    <File className="h-10 w-10" />
                </div>
                {files.length > 0 ? (
                    <div className="space-y-2">
                        <p className="text-2xl font-black text-foreground tracking-tight">{files[0].name}</p>
                        <p className="text-sm font-bold text-primary/60 uppercase tracking-widest">{files[0].size}</p>
                    </div>
                ) : (
                    <>
                        <p className="text-2xl font-black text-foreground mb-3 tracking-tight">Drop manuscript here or browse</p>
                        <p className="text-muted-foreground/40 font-medium">Secure local processing · Supports PDF, DOCX, TXT</p>
                    </>
                )}
            </div>
            {uploadError && <p className="text-destructive mt-4 font-bold">{uploadError}</p>}
          </motion.div>
        ) : (
          <motion.div
            key="text-input"
            initial={{ opacity: 0, scale: 0.98, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -10 }}
            className="glass-panel p-6 border-white/5 focus-within:border-primary/50 transition-colors shadow-sm"
          >
            <label className="block text-sm font-bold text-foreground mb-4 pl-2">Paste Manuscript Content</label>
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste your abstract, introduction, body, and references here..."
              className="w-full min-h-[400px] p-6 rounded-2xl bg-foreground/5 border-none outline-none focus:ring-2 focus:ring-primary/50 text-sm leading-relaxed text-foreground placeholder-muted-foreground/50 resize-y"
            />
            {uploadError && <p className="text-destructive mt-4 font-bold pl-2">{uploadError}</p>}
          </motion.div>
        )}
      </AnimatePresence>

      {activeTab === "file" && <FormattingAgent />}

      <div className="space-y-10">
        <div className="space-y-2 text-center md:text-left">
            <h2 className="text-3xl font-black text-foreground tracking-tight">Template Selection</h2>
            <p className="text-muted-foreground/60 font-medium max-w-2xl">Our agents will ensure 100% compliance with these official guidelines.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {templateOptions.map((opt) => (
            <TemplateCard
              key={opt.title}
              title={opt.title}
              description={opt.description}
              isSelected={selectedStyle === opt.title}
              onSelect={() => setSelectedStyle(opt.title)}
              isCustom={opt.isCustom}
              previewContent={opt.previewContent}
            />
          ))}
        </div>
      </div>

      <div className="space-y-10 pt-16 border-t border-white/5">
        <div className="space-y-2 text-center">
            <h2 className="text-3xl font-black text-foreground tracking-tight">Processing Engine</h2>
            <p className="text-muted-foreground/60 font-medium">Choose between maximum privacy or maximum speed.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            <button
                onClick={() => setIsCloudMode(false)}
                className={`p-8 rounded-[2rem] border-2 transition-all duration-500 flex flex-col items-start gap-4 text-left group relative overflow-hidden ${
                    !isCloudMode
                        ? "border-primary bg-primary/5 shadow-2xl ring-1 ring-primary/20"
                        : "border-white/5 hover:border-white/10 bg-white/5 hover:bg-white/10"
                }`}
            >
                <div className={`h-14 w-14 rounded-2xl flex items-center justify-center transition-all duration-500 ${!isCloudMode ? "bg-primary text-primary-foreground shadow-glow" : "bg-white/5 text-muted-foreground"}`}>
                    <Shield className="h-7 w-7" />
                </div>
                <div>
                    <span className="block font-black text-xl text-foreground tracking-tight mb-1">Local Agent</span>
                    <p className="text-sm text-muted-foreground/60 leading-relaxed font-medium">Zero-leak privacy. Runs locally on your hardware using LLM agents.</p>
                </div>
                {!isCloudMode && (
                    <div className="absolute top-4 right-4 h-2 w-2 rounded-full bg-primary animate-pulse" />
                )}
            </button>

            <button
                onClick={() => setIsCloudMode(true)}
                className={`p-8 rounded-[2rem] border-2 transition-all duration-500 flex flex-col items-start gap-4 text-left group relative overflow-hidden ${
                    isCloudMode
                        ? "border-primary bg-primary/5 shadow-2xl ring-1 ring-primary/20"
                        : "border-white/5 hover:border-white/10 bg-white/5 hover:bg-white/10"
                }`}
            >
                <div className={`h-14 w-14 rounded-2xl flex items-center justify-center transition-all duration-500 ${isCloudMode ? "bg-primary text-primary-foreground shadow-glow" : "bg-white/5 text-muted-foreground"}`}>
                    <Cloud className="h-7 w-7" />
                </div>
                <div>
                    <span className="block font-black text-xl text-foreground tracking-tight mb-1">Online Agent</span>
                    <p className="text-sm text-muted-foreground/60 leading-relaxed font-medium">Blazing fast. Uses optimized cloud-based AI inference engines.</p>
                </div>
                {isCloudMode && (
                    <div className="absolute top-4 right-4 h-2 w-2 rounded-full bg-primary animate-pulse" />
                )}
            </button>
        </div>
      </div>

      <div className="pt-12 flex flex-col items-center gap-3 sticky bottom-8 z-20">
        {uploadError && (
          <p className="text-sm text-red-400 font-medium bg-red-500/10 border border-red-500/20 px-4 py-2 rounded-xl">
            {uploadError}
          </p>
        )}
        <Button
            size="lg"
            className="w-full max-w-md bg-primary text-primary-foreground hover:bg-primary/90 gap-4 h-16 rounded-[2rem] shadow-[0_20px_40px_rgba(var(--primary),0.3)] text-xl font-black transition-all hover:scale-[1.05] active:scale-[0.95] group"
            disabled={uploading || (!selectedStyle) || (activeTab === "file" && files.length === 0) || (activeTab === "text" && !rawText.trim())}
            onClick={handleStart}
        >
            {uploading ? (
              <><Loader2 className="h-6 w-6 animate-spin" /> Uploading...</>
            ) : (
              <>Generate Formatting <ArrowRight className="h-6 w-6 group-hover:translate-x-1 transition-transform" /></>
            )}
        </Button>
      </div>
    </div>
  );
};

export default UploadPage;
