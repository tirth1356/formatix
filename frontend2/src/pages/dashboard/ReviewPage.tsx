import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Loader2, Check, X, CheckCircle2, ChevronRight } from "lucide-react";
import { useWorkflow } from "@/contexts/WorkflowContext";
import { apiGetJob, apiFormatDocument, apiValidateCitations, apiValidateFormat } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

const ReviewPage = () => {
    const { jobId, isCloudMode, advanceTo } = useWorkflow();
    const navigate = useNavigate();
    const [jobData, setJobData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);

    // Track which corrections are accepted (by index)
    const [acceptedIndices, setAcceptedIndices] = useState<Set<number>>(new Set());

    useEffect(() => {
        if (!jobId || jobId === "preview") {
            setLoading(false);
            return;
        }

        const loadJob = async () => {
            try {
                const data = await apiGetJob(jobId);
                setJobData(data);

                // By default, accept all
                if (data?.corrections && Array.isArray(data.corrections)) {
                    setAcceptedIndices(new Set(data.corrections.map((_: any, i: number) => i)));
                }
            } catch (err) {
                console.error("Failed to fetch job data", err);
            } finally {
                setLoading(false);
            }
        };
        loadJob();
    }, [jobId]);

    const toggleAccept = (index: number) => {
        setAcceptedIndices(prev => {
            const next = new Set(prev);
            if (next.has(index)) {
                next.delete(index);
            } else {
                next.add(index);
            }
            return next;
        });
    };

    const acceptAll = () => {
        if (jobData?.corrections) {
            setAcceptedIndices(new Set(jobData.corrections.map((_: any, i: number) => i)));
        }
    };

    const rejectAll = () => {
        setAcceptedIndices(new Set());
    };

    const handleGenerateFinal = async () => {
        setProcessing(true);
        try {
            // 1. Verify structure and rules exist - if not, the workflow steps weren't completed
            if (!jobData?.structure || !jobData?.rules) {
                throw new Error(
                    "Missing manuscript structure or formatting rules. " +
                    "Please ensure all preprocessing steps completed successfully."
                );
            }

            // 2. Gather accepted corrections
            const allCorrections = jobData?.corrections || [];
            const acceptedCorrections = allCorrections.filter((_: any, i: number) => acceptedIndices.has(i));

            // 3. Format Document
            await apiFormatDocument(jobId!, acceptedCorrections, isCloudMode);

            // 4. Validation (Parallel)
            await Promise.all([
                apiValidateCitations(jobId!, isCloudMode),
                apiValidateFormat(jobId!, isCloudMode)
            ]);

            // 5. Navigate to results
            advanceTo("results");
            navigate("/dashboard/results");

        } catch (err) {
            console.error("Error generating final document:", err);
            alert(`Failed to generate final document: ${(err as Error).message}`);
        } finally {
            setProcessing(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col h-[60vh] items-center justify-center space-y-4">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <p className="text-muted-foreground font-mono animate-pulse">Loading AI Suggestions...</p>
            </div>
        );
    }

    if (processing) {
        return (
            <div className="flex flex-col h-[60vh] items-center justify-center space-y-6">
                <Loader2 className="h-16 w-16 animate-spin text-primary" />
                <div className="text-center">
                    <h2 className="text-2xl font-black text-foreground">Applying Selected Edits</h2>
                    <p className="text-muted-foreground mt-2">Rebuilding structure, generating LaTeX/DOCX, and running final validation checks...</p>
                </div>
            </div>
        );
    }

    const allCorrections = jobData?.corrections || [];

    if (allCorrections.length === 0) {
        return (
            <div className="max-w-4xl mx-auto space-y-6 text-center py-20">
                <div className="inline-flex h-20 w-20 rounded-full bg-green-500/10 items-center justify-center mb-4">
                    <CheckCircle2 className="h-10 w-10 text-green-500" />
                </div>
                <h1 className="text-3xl font-black text-foreground">Perfect Formatting!</h1>
                <p className="text-muted-foreground max-w-lg mx-auto mb-8">
                    The AI did not find any necessary language or styling corrections to match your selected template.
                </p>
                <Button onClick={handleGenerateFinal} className="h-14 px-8 rounded-2xl text-lg font-black" size="lg">
                    Generate Final Document <ChevronRight className="ml-2 h-5 w-5" />
                </Button>
            </div>
        );
    }

    const acceptedCount = acceptedIndices.size;
    const totalCount = allCorrections.length;

    return (
        <div className="max-w-5xl mx-auto space-y-8 pb-32">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-border/50 pb-6">
                <div>
                    <h1 className="text-4xl font-black text-foreground tracking-tight">Review Suggestions</h1>
                    <p className="text-lg text-muted-foreground/60 mt-1">Accept or reject language and formatting edits before generating the final manuscript.</p>
                </div>
                <div className="flex flex-col items-end gap-3">
                    <div className="text-sm font-bold text-muted-foreground bg-accent/20 px-4 py-2 rounded-xl">
                        <span className="text-primary">{acceptedCount}</span> of {totalCount} accepted
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={rejectAll} className="h-9 px-4 rounded-xl font-bold">Reject All</Button>
                        <Button variant="default" size="sm" onClick={acceptAll} className="h-9 px-4 rounded-xl font-bold">Accept All</Button>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {allCorrections.map((c: any, i: number) => {
                    const isAccepted = acceptedIndices.has(i);
                    const typeLabel = c.type || "Format/Language";

                    return (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className={`glass-panel p-5 grid grid-cols-1 md:grid-cols-[1fr_auto] gap-6 items-center transition-all ${isAccepted ? 'border-primary/50 bg-primary/5' : 'border-border/50 opacity-60 grayscale-[0.8]'}`}
                        >
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-md ${isAccepted ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
                                        {typeLabel}
                                    </span>
                                    <span className="text-sm font-medium text-muted-foreground/80 flex-1">{c.reason || c.rule || "Style enforcement"}</span>
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <p className="text-[10px] font-bold text-destructive uppercase tracking-widest">Original Text</p>
                                        <p className="text-sm font-mono line-through text-destructive/80 bg-destructive/10 p-3 rounded-lg border border-destructive/20 break-words">
                                            {c.original || "-"}
                                        </p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className={`text-[10px] font-bold uppercase tracking-widest ${isAccepted ? 'text-green-500' : 'text-muted-foreground'}`}>Proposed Change</p>
                                        <p className={`text-sm font-mono font-bold p-3 rounded-lg border break-words ${isAccepted ? 'text-green-500 bg-green-500/10 border-green-500/20' : 'text-muted-foreground bg-muted/50 border-transparent'}`}>
                                            {c.change || c.corrected || "-"}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="flex md:flex-col gap-3 justify-end md:justify-center border-t md:border-t-0 md:border-l border-border/50 pt-4 md:pt-0 md:pl-6">
                                <Button
                                    onClick={() => toggleAccept(i)}
                                    variant={isAccepted ? "default" : "outline"}
                                    className={`flex-1 md:flex-none h-12 w-full md:w-16 rounded-xl transition-all ${isAccepted ? 'bg-green-500 hover:bg-green-600 text-white shadow-lg shadow-green-500/20' : ''}`}
                                >
                                    <Check className="h-6 w-6" />
                                    <span className="md:hidden ml-2 font-bold">Accept</span>
                                </Button>
                                <Button
                                    onClick={() => toggleAccept(i)}
                                    variant={!isAccepted ? "destructive" : "outline"}
                                    className={`flex-1 md:flex-none h-12 w-full md:w-16 rounded-xl transition-all border-border/50 ${!isAccepted ? 'shadow-lg shadow-destructive/20' : 'hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30'}`}
                                >
                                    <X className="h-6 w-6" />
                                    <span className="md:hidden ml-2 font-bold">Reject</span>
                                </Button>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            <div className="fixed bottom-0 left-0 lg:left-64 right-0 p-6 bg-background/80 backdrop-blur-xl border-t border-white/5 z-40 flex justify-center">
                <Button
                    onClick={handleGenerateFinal}
                    className="h-16 px-12 rounded-2xl text-xl font-black bg-primary hover:bg-primary/90 text-primary-foreground shadow-2xl transition-all hover:scale-[1.02] active:scale-[0.98] w-full max-w-md group"
                >
                    Generate Final Document
                    <ChevronRight className="ml-2 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                </Button>
            </div>
        </div>
    );
};

export default ReviewPage;
