import { Network } from "lucide-react";

type ServiceNode = {
  service_name?: string;
  name?: string;
  type?: string;
  confidence?: number;
};

export function BlastRadiusGraph({
  primaryService,
  impactedServices,
  serviceMap,
}: {
  primaryService: string;
  impactedServices?: string[];
  serviceMap?: ServiceNode[];
}) {
  const nodes: { name: string; confidence: number; type: string }[] = [];

  if (serviceMap?.length) {
    serviceMap.forEach((n) => {
      const name = n.service_name || n.name || "unknown";
      if (name !== primaryService) {
        nodes.push({
          name,
          confidence: n.confidence ?? 0.5,
          type: n.type ?? "downstream",
        });
      }
    });
  } else if (impactedServices?.length) {
    impactedServices.forEach((s, i) => {
      if (s !== primaryService) {
        nodes.push({
          name: s,
          confidence: Math.max(0.3, 1 - i * 0.12),
          type: "impacted",
        });
      }
    });
  }

  if (nodes.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
          <Network className="w-4 h-4 text-slate-400" />
          Blast Radius
        </h3>
        <p className="text-sm text-slate-500">No dependency data available for this incident.</p>
      </div>
    );
  }

  const cx = 200;
  const cy = 160;
  const radius = 110;

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0D1117] p-5">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
        <Network className="w-4 h-4 text-slate-400" />
        Blast Radius
      </h3>

      <div className="flex justify-center">
        <svg viewBox="0 0 400 320" className="w-full max-w-md" role="img" aria-label="Blast radius graph">
          <circle cx={cx} cy={cy} r={radius + 20} fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="4 4" />
          <circle cx={cx} cy={cy} r={radius - 20} fill="none" stroke="#1e293b" strokeWidth="1" strokeDasharray="4 4" />

          {nodes.map((node, i) => {
            const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
            const r = radius * (1.1 - node.confidence * 0.3);
            const nx = cx + r * Math.cos(angle);
            const ny = cy + r * Math.sin(angle);
            const opacity = 0.3 + node.confidence * 0.7;
            const color =
              node.confidence >= 0.7
                ? "#ef4444"
                : node.confidence >= 0.4
                ? "#f59e0b"
                : "#64748b";

            return (
              <g key={node.name}>
                <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={color} strokeWidth="1.5" opacity={opacity * 0.6} />
                <circle cx={nx} cy={ny} r={18} fill={color} opacity={opacity * 0.2} stroke={color} strokeWidth="1" />
                <circle cx={nx} cy={ny} r={4} fill={color} opacity={opacity} />
                <text
                  x={nx}
                  y={ny + 28}
                  textAnchor="middle"
                  className="text-[9px] fill-slate-400"
                  style={{ fontSize: "9px" }}
                >
                  {node.name.length > 18 ? node.name.slice(0, 16) + "…" : node.name}
                </text>
                <text
                  x={nx}
                  y={ny + 39}
                  textAnchor="middle"
                  className="text-[8px]"
                  style={{ fontSize: "8px", fill: color }}
                >
                  {Math.round(node.confidence * 100)}%
                </text>
              </g>
            );
          })}

          <circle cx={cx} cy={cy} r={22} fill="#ef4444" opacity={0.15} stroke="#ef4444" strokeWidth="1.5" />
          <circle cx={cx} cy={cy} r={6} fill="#ef4444" />
          <text
            x={cx}
            y={cy + 36}
            textAnchor="middle"
            className="text-[10px] fill-white font-medium"
            style={{ fontSize: "10px" }}
          >
            {primaryService.length > 20 ? primaryService.slice(0, 18) + "…" : primaryService}
          </text>
        </svg>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        {nodes.slice(0, 8).map((node) => (
          <span
            key={node.name}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-slate-800/60 text-xs text-slate-300"
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor:
                  node.confidence >= 0.7 ? "#ef4444" : node.confidence >= 0.4 ? "#f59e0b" : "#64748b",
              }}
            />
            {node.name}
          </span>
        ))}
      </div>
    </div>
  );
}
