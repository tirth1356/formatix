import { motion } from "framer-motion";
import { Check, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";

interface TemplateCardProps {
  title: string;
  description: string[];
  isSelected: boolean;
  onSelect: () => void;
  isCustom?: boolean;
  previewContent?: React.ReactNode;
}

const TemplateCard = ({
  title,
  description,
  isSelected,
  onSelect,
  isCustom,
  previewContent,
}: TemplateCardProps) => {
  return (
    <motion.div
      whileHover={{ y: -6, scale: 1.02 }}
      className={`glass-panel p-8 transition-all duration-500 flex flex-col h-full cursor-pointer relative overflow-hidden group ${
        isSelected 
          ? "border-primary/50 shadow-[0_20px_40px_rgba(var(--primary),0.15)] ring-1 ring-primary/20" 
          : "border-white/5 hover:border-primary/20 hover:shadow-2xl"
      }`}
      onClick={onSelect}
    >
      <Dialog>
        <DialogTrigger asChild>
          <div 
            className="aspect-[16/10] bg-muted/20 rounded-2xl mb-8 flex flex-col gap-3 p-6 overflow-hidden relative border border-white/5 shadow-inner group/preview"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Placeholder for template preview */}
            <div className="w-full h-2.5 bg-foreground/10 rounded-full animate-pulse" />
            <div className="w-3/4 h-2.5 bg-foreground/10 rounded-full animate-pulse delay-75" />
            <div className="w-full h-12 bg-foreground/5 rounded-xl mt-3 flex items-center justify-center">
                 <div className="w-1/3 h-2 bg-foreground/10 rounded-full" />
            </div>
            <div className="grid grid-cols-2 gap-3 mt-auto">
              <div className="h-8 bg-foreground/5 rounded-lg" />
              <div className="h-8 bg-foreground/5 rounded-lg" />
            </div>
            
            {/* Hover Overlay */}
            <div className="absolute inset-0 bg-primary/10 opacity-0 group-hover/preview:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]">
              <div className="bg-background/80 p-3 rounded-full shadow-xl border border-primary/20 scale-90 group-hover/preview:scale-100 transition-transform">
                <Eye className="h-6 w-6 text-primary" />
              </div>
            </div>

            {isSelected && (
              <div className="absolute top-4 right-4 bg-primary text-primary-foreground text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest shadow-lg z-10">
                ACTIVE
              </div>
            )}
          </div>
        </DialogTrigger>
        <DialogContent className="max-w-3xl border-white/10 bg-background/95 backdrop-blur-2xl p-0 overflow-hidden rounded-[2rem]">
          <DialogHeader className="p-8 pb-0">
            <DialogTitle className="text-3xl font-black tracking-tight">{title} Preview</DialogTitle>
          </DialogHeader>
          <div className="p-8">
            {previewContent || (
              <div className="aspect-video bg-muted/30 rounded-3xl border border-white/5 flex items-center justify-center p-12 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent" />
                <div className="relative z-10 w-full space-y-6">
                  <div className="h-4 w-1/3 bg-foreground/20 rounded-full" />
                  <div className="space-y-3">
                    <div className="h-3 w-full bg-foreground/10 rounded-full" />
                    <div className="h-3 w-full bg-foreground/10 rounded-full" />
                    <div className="h-3 w-2/3 bg-foreground/10 rounded-full" />
                  </div>
                  <div className="grid grid-cols-2 gap-6 pt-6">
                    <div className="h-32 bg-foreground/5 rounded-2xl border border-white/5 shadow-inner" />
                    <div className="h-32 bg-foreground/5 rounded-2xl border border-white/5 shadow-inner" />
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="p-8 pt-0 flex justify-end">
            <DialogClose asChild>
              <Button 
                onClick={() => onSelect()} 
                className="bg-primary text-primary-foreground font-bold px-8 h-12 rounded-xl shadow-lg hover:shadow-primary/20 transition-all hover:scale-105"
              >
                Use This Template
              </Button>
            </DialogClose>
          </div>
        </DialogContent>
      </Dialog>

      <h3 className="text-xl font-black text-foreground mb-4 tracking-tight drop-shadow-sm">{title}</h3>
      
      <ul className="space-y-3.5 mb-10 flex-grow">
        {description.map((item, idx) => (
          <li key={idx} className="flex items-start gap-3.5 text-sm text-foreground/80 leading-relaxed font-medium">
            <div className={`mt-0.5 h-5 w-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-transform group-hover:scale-110 ${
              isSelected ? "border-primary bg-primary/20 shadow-glow" : "border-foreground/10"
            }`}>
              <Check className={`h-3 w-3 ${isSelected ? "text-primary stroke-[4px]" : "text-transparent"}`} />
            </div>
            <span>{item}</span>
          </li>
        ))}
        {isCustom && (
            <li className="flex items-start gap-3.5 text-sm text-primary font-bold mt-4 px-4 py-2 rounded-xl bg-primary/5 border border-primary/10">
                <span>Upload guideline PDF</span>
            </li>
        )}
      </ul>

      <Button
        variant={isSelected ? "default" : "outline"}
        className={`w-full rounded-2xl h-14 text-base font-bold transition-all duration-500 shadow-lg ${
          isSelected 
            ? "bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-primary/20" 
            : "border-white/10 text-foreground hover:bg-white/5 hover:border-white/20"
        }`}
        onClick={(e) => {
          e.stopPropagation();
          onSelect();
        }}
      >
        {isSelected ? "Selected" : "Use This Template"}
      </Button>
    </motion.div>
  );
};

export default TemplateCard;
