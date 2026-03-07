import { motion } from "framer-motion";
import { FileText, Zap, BarChart3, Clock, Upload, CheckCircle2, AlertTriangle, TrendingUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const stats = [
  { label: "Documents Processed", value: "247", icon: FileText, change: "+12%" },
  { label: "Avg Format Score", value: "94.2%", icon: BarChart3, change: "+3.1%" },
  { label: "Active Agents", value: "6/6", icon: Zap, change: "Online" },
  { label: "Avg Processing", value: "8.3s", icon: Clock, change: "-1.2s" },
];

const weeklyData = [
  { day: "Mon", docs: 32 }, { day: "Tue", docs: 45 }, { day: "Wed", docs: 28 },
  { day: "Thu", docs: 51 }, { day: "Fri", docs: 39 }, { day: "Sat", docs: 15 }, { day: "Sun", docs: 12 },
];

const formatDist = [
  { name: "APA", value: 35, color: "hsl(165, 80%, 48%)" },
  { name: "IEEE", value: 25, color: "hsl(200, 90%, 55%)" },
  { name: "MLA", value: 18, color: "hsl(260, 80%, 62%)" },
  { name: "Chicago", value: 12, color: "hsl(25, 95%, 58%)" },
  { name: "Vancouver", value: 10, color: "hsl(185, 90%, 55%)" },
];

const recentDocs = [
  { name: "Neural_Networks_Review.docx", format: "APA", score: 96, status: "complete" },
  { name: "Climate_Study_2024.pdf", format: "IEEE", score: 91, status: "complete" },
  { name: "Genomics_Paper.docx", format: "Vancouver", score: 88, status: "warning" },
  { name: "AI_Ethics_Manuscript.txt", format: "MLA", score: 94, status: "complete" },
];

const Overview = () => {
  return (
    <div className="space-y-6 max-w-7xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Next Gen Document Formatter — Agent Pipeline Overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }} className="glass-panel p-5">
            <div className="flex items-center justify-between mb-3">
              <s.icon className="h-5 w-5 text-primary" />
              <span className="text-xs text-primary font-mono">{s.change}</span>
            </div>
            <p className="text-2xl font-bold text-foreground">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-panel p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-foreground mb-4">Weekly Processing Volume</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(225 15% 16%)" />
              <XAxis dataKey="day" stroke="hsl(215 20% 55%)" fontSize={12} />
              <YAxis stroke="hsl(215 20% 55%)" fontSize={12} />
              <Tooltip contentStyle={{ background: "hsl(225 20% 9%)", border: "1px solid hsl(225 15% 20%)", borderRadius: 8, color: "hsl(210 40% 96%)" }} />
              <Bar dataKey="docs" fill="hsl(165, 80%, 48%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="glass-panel p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Format Distribution</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={formatDist} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value" stroke="none">
                {formatDist.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "hsl(225 20% 9%)", border: "1px solid hsl(225 15% 20%)", borderRadius: 8, color: "hsl(210 40% 96%)" }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {formatDist.map((f) => (
              <span key={f.name} className="flex items-center gap-1 text-xs text-muted-foreground">
                <span className="h-2 w-2 rounded-full" style={{ background: f.color }} />
                {f.name}
              </span>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Recent Documents */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="glass-panel p-5">
        <h3 className="text-sm font-semibold text-foreground mb-4">Recent Documents</h3>
        <div className="space-y-2">
          {recentDocs.map((doc) => (
            <div key={doc.name} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-3">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium text-foreground">{doc.name}</p>
                  <p className="text-xs text-muted-foreground">{doc.format} format</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-sm font-mono font-bold ${doc.score >= 90 ? "text-primary" : "text-neon-orange"}`}>{doc.score}%</span>
                {doc.status === "complete" ? <CheckCircle2 className="h-4 w-4 text-primary" /> : <AlertTriangle className="h-4 w-4 text-neon-orange" />}
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default Overview;
