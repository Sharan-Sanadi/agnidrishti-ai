import Link from 'next/link';
import { ArrowRight, MapPin, Sliders, Layers, BrainCircuit, BarChart3 } from 'lucide-react';

export function PlatformPreviewSection() {
  const highlights = [
    {
      icon: MapPin,
      title: "Interactive GIS Map View",
      desc: "Leaflet map with PostGIS spatial rendering, custom satellite imagery layers, and observation markers.",
    },
    {
      icon: Sliders,
      title: "Multi-Source Context Filters",
      desc: "Filter observations by persistence, industrial proximity, land-cover class, Sentinel-2 clarity, and ML prediction.",
    },
    {
      icon: Layers,
      title: "Observation Analysis Drawer",
      desc: "Detailed side drawer presenting exact multi-phase intelligence metrics for any selected thermal observation.",
    },
    {
      icon: BrainCircuit,
      title: "Model-Faithful Explainability",
      desc: "Tree-SHAP attributions breaking down top supporting and opposing evidence for each classification.",
    },
  ];

  return (
    <section className="py-24 bg-white border-y border-neutral-200 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Storytelling & CTA */}
          <div className="lg:col-span-5 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200 text-orange-600 text-xs font-mono">
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Operational GIS Dashboard</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight">
              Built for Investigation, Not Just Visualization
            </h2>
            <p className="text-neutral-600 text-base leading-relaxed">
              The Agnidrishti platform provides an intuitive, high-density geospatial workstation for environmental analysts, industrial auditors, and emergency coordinators.
            </p>

            {/* Feature Callouts */}
            <div className="space-y-4 pt-2">
              {highlights.map((item, idx) => {
                const Icon = item.icon;
                return (
                  <div key={idx} className="flex items-start gap-3.5 p-3 rounded-xl bg-neutral-50 border border-neutral-200">
                    <div className="p-2 rounded-lg bg-orange-50 text-orange-600 border border-orange-200 shrink-0">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-neutral-900">{item.title}</h3>
                      <p className="text-xs text-neutral-600 leading-snug">{item.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Single Explicit CTA Button */}
            <div className="pt-4">
              <Link
                href="/dashboard"
                className="group relative inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 text-white font-bold text-sm tracking-wide shadow-xl shadow-orange-950/50 hover:shadow-amber-500/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                <span>Open Dashboard</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>

          {/* Right Column: Platform Dashboard Interactive Preview Graphic */}
          <div className="lg:col-span-7">
            <div className="rounded-2xl bg-white border border-neutral-200 p-5 shadow-xl space-y-4">
              {/* Dashboard Topbar */}
              <div className="flex items-center justify-between border-b border-neutral-200 pb-3">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="text-xs font-mono text-neutral-600 font-semibold">AGNIDRISHTI PLATFORM</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] font-mono">
                  <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">POSTGIS ACTIVE</span>
                  <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">1,500 OBS</span>
                </div>
              </div>

              {/* Layout Mockup: Left Filter Sidebar + Main Map Canvas + Right Drawer */}
              <div className="grid grid-cols-12 gap-3 h-80">
                {/* Left Sidebar */}
                <div className="col-span-3 bg-slate-900/90 rounded-xl border border-slate-800 p-2.5 space-y-2 text-[10px] font-mono">
                  <div className="text-slate-400 uppercase font-bold border-b border-slate-800 pb-1">Filters</div>
                  <div className="p-1.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-semibold">
                    Live FIRMS (1 Day)
                  </div>
                  <div className="p-1.5 rounded bg-slate-950 text-slate-300 border border-slate-800">
                    Persistence: All
                  </div>
                  <div className="p-1.5 rounded bg-slate-950 text-slate-300 border border-slate-800">
                    Industry: Mapped
                  </div>
                  <div className="p-1.5 rounded bg-slate-950 text-slate-300 border border-slate-800">
                    WorldCover: Built-up
                  </div>
                  <div className="p-1.5 rounded bg-slate-950 text-slate-300 border border-slate-800">
                    Sentinel-2: Clear
                  </div>
                </div>

                {/* Main Map View */}
                <div className="col-span-6 bg-slate-900 rounded-xl border border-slate-800 relative overflow-hidden flex flex-col justify-between p-3">
                  <div className="absolute inset-0 bg-[radial-gradient(#334155_1px,transparent_1px)] [background-size:12px_12px] opacity-40" />

                  {/* Marker Pin */}
                  <div className="absolute top-1/3 left-1/2 -translate-x-1/2 flex items-center justify-center">
                    <div className="w-8 h-8 rounded-full border border-amber-500/50 bg-amber-500/20 animate-ping absolute" />
                    <div className="w-4 h-4 rounded-full bg-amber-500 border-2 border-white shadow-lg" />
                  </div>

                  <div className="relative z-10 flex justify-between text-[10px] font-mono text-slate-300">
                    <span className="bg-slate-950/80 px-2 py-0.5 rounded border border-slate-800">22.5726° N, 88.3639° E</span>
                    <span className="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/40">VIIRS NOAA-20</span>
                  </div>

                  <div className="relative z-10 mt-auto bg-slate-950/90 p-2 rounded-lg border border-slate-800 text-[10px] font-mono flex items-center justify-between">
                    <span className="text-slate-400">Class:</span>
                    <span className="text-emerald-400 font-bold">INDUSTRIAL_THERMAL</span>
                  </div>
                </div>

                {/* Right Analysis Drawer Preview */}
                <div className="col-span-3 bg-slate-900/90 rounded-xl border border-slate-800 p-2.5 space-y-2 text-[10px] font-mono">
                  <div className="text-amber-400 uppercase font-bold border-b border-slate-800 pb-1">Observation Drawer</div>
                  <div className="text-slate-300">FRP: <span className="text-amber-300 font-bold">54.2 MW</span></div>
                  <div className="text-slate-300">Persistence: <span className="text-emerald-300 font-bold">92%</span></div>
                  <div className="text-slate-300">OSM Dist: <span className="text-cyan-300 font-bold">85m Power Plant</span></div>
                  <div className="text-slate-300">WorldCover: <span className="text-teal-300 font-bold">Built-up (82%)</span></div>
                  <div className="p-1.5 rounded bg-violet-500/10 text-violet-300 border border-violet-500/30 text-[9px] leading-tight mt-2">
                    Tree-SHAP: Top driver is osm_industrial_dist_m (-0.421)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
