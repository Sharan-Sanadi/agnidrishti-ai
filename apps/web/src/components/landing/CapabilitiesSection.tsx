import { Flame, Clock, Factory, Trees, Satellite, Layers, BrainCircuit, Sparkles } from 'lucide-react';

export function CapabilitiesSection() {
  const capabilities = [
    {
      icon: Flame,
      phase: "Phase 1 & 2",
      title: "Thermal Intelligence",
      description:
        "Streams and stores NASA FIRMS VIIRS observations with acquisition time, sensor metadata, FRP and PostGIS geospatial coordinates.",
      tag: "Live VIIRS Data",
      color: "border-amber-200 text-amber-400 bg-amber-50",
    },
    {
      icon: Clock,
      phase: "Phase 3",
      title: "Temporal Persistence",
      description:
        "Analyzes 30-day historical detection frequency to distinguish isolated anomalies from routine, recurrent thermal sources.",
      tag: "Spatial-Temporal",
      color: "border-orange-200 text-orange-400 bg-orange-50",
    },
    {
      icon: Factory,
      phase: "Phase 4",
      title: "Industrial Proximity",
      description:
        "Associates thermal observations with nearby industrial infrastructure and geospatial proximity using OpenStreetMap context.",
      tag: "OSM Infrastructure",
      color: "border-cyan-200 text-cyan-400 bg-cyan-50",
    },
    {
      icon: Trees,
      phase: "Phase 5",
      title: "Land-Cover Baseline",
      description:
        "Samples ESA WorldCover 2021 as a stable 10m land-cover baseline across 250m, 500m, and 1000m circular radii.",
      tag: "ESA 10m Baseline",
      color: "border-emerald-200 text-emerald-400 bg-emerald-50",
    },
    {
      icon: Satellite,
      phase: "Phase 6",
      title: "Sentinel-2 Context",
      description:
        "Evaluates Copernicus Sentinel-2 L2A optical, NIR, and SWIR surface reflectance including NDVI, NDMI, and NBR evidence.",
      tag: "Copernicus L2A",
      color: "border-teal-200 text-teal-400 bg-teal-50",
    },
    {
      icon: Layers,
      phase: "Phase 7",
      title: "Feature Fusion Engine",
      description:
        "Combines 34 multi-source evidence channels into a deterministic, versioned feature profile for downstream intelligence.",
      tag: "fusion_v1 Matrix",
      color: "border-indigo-200 text-indigo-400 bg-indigo-50",
    },
    {
      icon: BrainCircuit,
      phase: "Phase 8 & 9",
      title: "ML & Explainable AI",
      description:
        "Applies a reproducible Random Forest model to classify thermal archetypes and surfaces exact Tree-SHAP feature attributions.",
      tag: "Tree-SHAP Attributions",
      color: "border-violet-200 text-violet-400 bg-violet-50",
    },
  ];

  return (
    <section id="capabilities" className="py-24 bg-neutral-50 border-y border-neutral-200 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-50 border border-violet-200 text-violet-700 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Platform Core Capabilities</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight">
            Geospatial Intelligence Capabilities
          </h2>
          <p className="text-neutral-600 text-base leading-relaxed">
            Every capability in Agnidrishti is grounded in real, functioning code and verified datasets across Phases 1 through 9.
          </p>
        </div>

        {/* 7 Capabilities Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {capabilities.map((cap, idx) => {
            const Icon = cap.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-white border border-neutral-200 hover:border-neutral-300 hover:shadow-md hover:-translate-y-0.5 transition-all shadow-sm flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className={`w-12 h-12 rounded-xl border flex items-center justify-center ${cap.color}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-neutral-100 text-neutral-500 border border-neutral-200">
                      {cap.phase}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-neutral-900">{cap.title}</h3>
                  <p className="text-xs text-neutral-600 leading-relaxed">{cap.description}</p>
                </div>
                <div className="mt-6 pt-4 border-t border-neutral-100 flex items-center justify-between text-[11px] font-mono">
                  <span className="text-neutral-400">DATA SOURCE</span>
                  <span className="text-orange-600 font-semibold">{cap.tag}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
