import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { DashboardSidebar } from "@/components/DashboardSidebar";
import { Outlet } from "react-router-dom";
import { Menu } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

const DashboardLayout = () => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background bg-grid-pattern">
        <DashboardSidebar />
        <div className="flex-1 flex flex-col min-h-screen">
          <header className="h-20 flex items-center border-b border-white/5 px-8 bg-background/40 backdrop-blur-xl sticky top-0 z-30">
            <div className="flex items-center gap-4">
              <SidebarTrigger className="h-10 w-10 rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-all">
                <Menu className="h-6 w-6" />
              </SidebarTrigger>
            </div>

            <div className="ml-auto flex items-center gap-6">
              <ThemeToggle />
            </div>
          </header>
          <main className="flex-1 p-6 overflow-auto scrollbar-thin">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default DashboardLayout;
