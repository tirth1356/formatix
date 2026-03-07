import { FileText, Upload, Settings, BarChart3, GitCompare, Cpu, BookOpen, Shield, History, Zap, RotateCcw, LayoutGrid } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation, useNavigate } from "react-router-dom";
import { useWorkflow, WorkflowStage } from "@/contexts/WorkflowContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

type NavItem = { title: string; url: string; icon: any; minStage: WorkflowStage };

const workflowItems: NavItem[] = [
  { title: "Upload", url: "/dashboard/upload", icon: Upload, minStage: "upload" },
  { title: "Processing", url: "/dashboard/processing", icon: Cpu, minStage: "processing" },
  { title: "Results", url: "/dashboard/results", icon: FileText, minStage: "results" },
  { title: "Elements", url: "/dashboard/elements", icon: LayoutGrid, minStage: "results" },
  { title: "Compare", url: "/dashboard/compare", icon: GitCompare, minStage: "results" },
];

const analyticsItems: NavItem[] = [
  { title: "Format Score", url: "/dashboard/score", icon: BarChart3, minStage: "results" },
  { title: "Corrections", url: "/dashboard/corrections", icon: BookOpen, minStage: "results" },
];

const systemItems: NavItem[] = [
  { title: "AI Agents", url: "/dashboard/agents", icon: Zap, minStage: "complete" },
  { title: "Security", url: "/dashboard/security", icon: Shield, minStage: "complete" },
  { title: "Settings", url: "/dashboard/settings", icon: Settings, minStage: "upload" },
];

const stageOrder: WorkflowStage[] = ["upload", "processing", "results", "complete"];

function isVisible(minStage: WorkflowStage, currentStage: WorkflowStage) {
  return stageOrder.indexOf(currentStage) >= stageOrder.indexOf(minStage);
}

export function DashboardSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const location = useLocation();
  const navigate = useNavigate();
  const { stage, resetWorkflow } = useWorkflow();
  const isActive = (path: string) => location.pathname === path;

  const renderGroup = (label: string, items: NavItem[]) => {
    const visibleItems = items.filter((item) => isVisible(item.minStage, stage));
    if (visibleItems.length === 0) return null;

    return (
      <SidebarGroup>
        <SidebarGroupLabel className="text-[11px] uppercase tracking-widest text-muted-foreground/50 font-medium">
          {label}
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <AnimatePresence>
              {visibleItems.map((item, i) => (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.3 }}
                >
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={item.url}
                        end
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                          collapsed ? "justify-center" : ""
                        } ${
                          isActive(item.url)
                            ? "bg-primary/10 text-primary shadow-sm"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                        }`}
                        activeClassName="bg-primary/10 text-primary"
                      >
                        <item.icon className="h-4 w-4 shrink-0" />
                        {!collapsed && <span className="text-[13px] font-medium">{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </motion.div>
              ))}
            </AnimatePresence>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  };

  return (
    <Sidebar collapsible="icon" className="border-r border-white/5 bg-background/50 backdrop-blur-xl shadow-2xl">
      <SidebarContent className="pt-8 flex flex-col h-full">
        {/* Logo — collapsed state uses smaller icon to avoid clipping (sidebar icon width = 3rem) */}
        <div className="px-6 mb-10 flex items-center justify-center group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:mb-6 group-data-[collapsible=icon]:min-w-[var(--sidebar-width-icon)]">
          {!collapsed ? (
            <div className="flex items-center gap-3 group cursor-pointer min-w-0" onClick={() => navigate("/")}>
              <div className="h-11 w-11 shrink-0 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-lg group-hover:scale-110 transition-transform duration-500">
                <Zap className="h-6 w-6 text-primary" />
              </div>
              <div className="overflow-hidden min-w-0">
                <h2 className="text-base font-black text-foreground tracking-tighter leading-tight truncate">FormatIX</h2>
                <p className="text-[11px] font-bold text-primary/50 uppercase tracking-widest">Document Formatter</p>
              </div>
            </div>
          ) : (
            <div className="h-8 w-8 shrink-0 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-lg hover:scale-105 transition-transform cursor-pointer" onClick={() => navigate("/")}>
              <Zap className="h-4 w-4 text-primary" />
            </div>
          )}
        </div>

        {/* Nav groups */}
        <div className="flex-1 space-y-2 px-2">
          {renderGroup("Main Workflow", workflowItems)}
          {renderGroup("Deep Analysis", analyticsItems)}
          {renderGroup("Intelligence System", systemItems)}
        </div>

        {/* Bottom section */}
        <div className="p-4 border-t border-white/5 space-y-3 bg-background/20">
          {!collapsed && (
            <button
              onClick={() => {
                resetWorkflow();
                navigate("/dashboard/upload");
              }}
              className="flex items-center justify-center gap-3 w-full h-12 rounded-2xl bg-white/5 text-muted-foreground hover:text-foreground hover:bg-white/10 transition-all duration-300 font-bold text-xs ring-1 ring-white/10 hover:ring-primary/40 shadow-sm overflow-hidden whitespace-nowrap"
            >
              <RotateCcw className="h-4 w-4" />
              <span>NEW MANUSCRIPT</span>
            </button>
          )}
        </div>
      </SidebarContent>
    </Sidebar>
  );
}
