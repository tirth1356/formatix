import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  Server, 
  Cloud, 
  Zap, 
  Save, 
  User, 
  Moon, 
  Sun, 
  Monitor, 
  Bell, 
  Lock, 
  Mail,
  Smartphone,
  ShieldCheck,
  CreditCard,
  LogOut
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const SettingsPage = () => {
  return (
    <div className="max-w-5xl mx-auto pb-20">
      <div className="mb-12">
        <h1 className="text-4xl font-black text-foreground tracking-tight mb-2">Pricing</h1>
        <p className="text-muted-foreground font-medium">Choose the plan that fits your needs.</p>
      </div>

      <div className="space-y-8">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
              <CreditCard className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-black text-foreground tracking-tight">Subscription & Billing</h2>
              <p className="text-xs text-muted-foreground font-medium">Manage your Enterprise AI license and usage.</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Basic Plan */}
            <div className="p-8 rounded-3xl bg-white/5 border-2 border-white/10 relative overflow-hidden group hover:border-primary/30 transition-all">
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 transition-transform duration-500">
                <Server className="h-32 w-32 text-foreground" />
              </div>
              <div className="relative z-10">
                <h3 className="text-2xl font-black text-foreground mb-1 tracking-tight">Basic</h3>
                <p className="text-sm text-muted-foreground mb-6">Essential formatting tools</p>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-black text-foreground">$5.99</span>
                  <span className="text-sm text-muted-foreground font-bold">/month</span>
                </div>
                <ul className="space-y-3 mb-8">
                  <li className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                    Document formatting
                  </li>
                  <li className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                    Citation styles (APA, MLA, IEEE)
                  </li>
                  <li className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="h-1.5 w-1.5 rounded-full bg-muted"></div>
                    <span className="line-through">Auto-correction</span>
                  </li>
                  <li className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="h-1.5 w-1.5 rounded-full bg-muted"></div>
                    <span className="line-through">Advanced analytics</span>
                  </li>
                </ul>
                <Button className="w-full h-12 bg-white/5 border-white/10 hover:bg-white/10 text-foreground rounded-xl font-bold">Select Plan</Button>
              </div>
            </div>

            {/* Pro Plan */}
            <div className="p-8 rounded-3xl bg-primary/10 border-2 border-primary/20 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform duration-500">
                <Zap className="h-32 w-32 text-primary" />
              </div>
              <div className="relative z-10">
                <Badge className="bg-primary text-primary-foreground mb-4 rounded-full px-4 py-1 font-black tracking-widest text-[10px] uppercase">Recommended</Badge>
                <h3 className="text-2xl font-black text-foreground mb-1 tracking-tight">Pro</h3>
                <p className="text-sm text-muted-foreground mb-6">Full access with AI features</p>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-black text-foreground">$10.99</span>
                  <span className="text-sm text-muted-foreground font-bold">/month</span>
                </div>
                <ul className="space-y-3 mb-8">
                  <li className="flex items-center gap-2 text-sm text-foreground font-medium">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                    Everything in Basic
                  </li>
                  <li className="flex items-center gap-2 text-sm text-foreground font-medium">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                    AI auto-correction
                  </li>
                  <li className="flex items-center gap-2 text-sm text-foreground font-medium">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                    Advanced analytics
                  </li>
                  <li className="flex items-center gap-2 text-sm text-foreground font-medium">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                    Priority support
                  </li>
                </ul>
                <Button className="w-full h-12 bg-primary text-primary-foreground hover:bg-primary/90 rounded-xl font-bold shadow-lg">Select Plan</Button>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="mt-12 flex justify-center p-8 glass-panel border-primary/20 bg-primary/5 sticky bottom-8 z-30 shadow-2xl backdrop-blur-xl rounded-[2.5rem]">
        <p className="text-sm text-muted-foreground font-medium">All plans include 14-day free trial • Cancel anytime • Secure payment</p>
      </div>
    </div>
  );
};

export default SettingsPage;
