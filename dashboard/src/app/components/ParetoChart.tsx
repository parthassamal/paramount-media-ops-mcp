import React from "react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp } from "lucide-react";

const paretoData = [
  {
    category: "High-Value Churners",
    impact: 425,
    cumulative: 44,
  },
  { category: "Price-Sensitive", impact: 288, cumulative: 74 },
  { category: "Content-Starved", impact: 162, cumulative: 91 },
  {
    category: "Platform Migration",
    impact: 90,
    cumulative: 100,
  },
];

export function ParetoChart() {
  return (
    <div className="bg-[#0D1117] border border-slate-800 rounded-xl p-6 shadow-lg h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-[#FF6B00]/10 p-2 rounded-lg">
            <TrendingUp className="w-5 h-5 text-[#FF6B00]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              Pareto Analysis
            </h2>
            <p className="text-sm text-slate-400">
              77% of impact from top 20% of cohorts
            </p>
          </div>
        </div>
      </div>

      <div className="h-64 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={paretoData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#334155"
            />
            <XAxis
              dataKey="category"
              stroke="#94a3b8"
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              angle={-15}
              textAnchor="end"
              height={80}
            />
            <YAxis
              yAxisId="left"
              stroke="#94a3b8"
              tick={{ fill: "#94a3b8" }}
              label={{
                value: "Impact ($M)",
                angle: -90,
                position: "insideLeft",
                fill: "#94a3b8",
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#94a3b8"
              tick={{ fill: "#94a3b8" }}
              label={{
                value: "Cumulative %",
                angle: 90,
                position: "insideRight",
                fill: "#94a3b8",
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                borderRadius: "8px",
                color: "#f1f5f9",
              }}
              formatter={(value: number, name: string) => {
                if (name === "impact")
                  return [`$${value}M`, "Impact"];
                if (name === "cumulative")
                  return [`${value}%`, "Cumulative"];
                return [value, name];
              }}
            />
            <Legend
              wrapperStyle={{ color: "#94a3b8" }}
              iconType="rect"
            />
            <Bar
              yAxisId="left"
              dataKey="impact"
              fill="#8b5cf6"
              radius={[8, 8, 0, 0]}
              name="Impact ($M)"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cumulative"
              stroke="#f59e0b"
              strokeWidth={3}
              dot={{ fill: "#f59e0b", r: 6 }}
              name="Cumulative %"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 bg-[#0064FF]/10 border border-[#0064FF]/30 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-slate-400">
              Top 2 Cohorts (50% of segments)
            </div>
            <div className="font-bold text-[#0064FF]">
              $713M Impact (74%)
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-400">
              Pareto Principle
            </div>
            <div className="font-bold text-[#FF6B00]">
              80/20 Rule Applied
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}