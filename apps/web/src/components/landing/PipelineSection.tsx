"use client";

import { useState } from 'react';
import { Flame, Database, Clock, Factory, Trees, Satellite, Layers, BrainCircuit, Sparkles, CheckCircle2 } from 'lucide-react';

export function PipelineSection() {
  const [activeStep, setActiveStep] = useState<number>(0);

  const steps = [
    {
      phase: "Phase 1",
      name: "NASA FIRMS Ingestion",
      icon: Flame,
      color: "text-amber-400 border-amber-200 bg-amber-50",
      summary: "Streams VIIRS NRT thermal detections with FRP, acquisition time, and sensor coordinates.",
      details: "Retrieves near-real-time thermal hotspots from NOAA-20 / NOAA-21 VIIRS sensors, recording Fire Radiative Power (MW) and brightness temperature."
    },
    {
      phase: "Phase 2",
      name: "PostGIS Storage",
      icon: Database,
      color: "text-blue-400 border-blue-200 bg-blue-50",
      summary: "Persists spatial points in PostGIS geometry columns with SRID 4326 indexing.",
      details: "Ensures idempotent deduplication, spatial indexing, and canonical observation records with zero data loss or coordinate drift."
    },
    {
      phase: "Phase 3",
      name: "Temporal Persistence",
      icon: Clock,
      color: "text-orange-400 border-orange-200 bg-orange-50",
      summary: "Analyzes 30-day spatial history to identify isolated, recurring, or persistent thermal behavior.",
      details: "Computes temporal persistence profiles across spatial radius thresholds to separate one-time thermal spikes from routine industrial operations."
    },
    {
      phase: "Phase 4",
      name: "Industrial Context",
      icon: Factory,
      color: "text-cyan-400 border-cyan-200 bg-cyan-50",
      summary: "Maps nearby industrial infrastructure and geospatial proximity using OpenStreetMap data.",
      details: "Extracts power plants, refineries, metal works, and chemical facilities within multi-ring geospatial buffers around thermal detections."
    },
    {
      phase: "Phase 5",
      name: "ESA WorldCover Baseline",
      icon: Trees,
      color: "text-emerald-400 border-emerald-200 bg-emerald-50",
      summary: "Samples 10m 2021 land-cover composition at 250m, 500m, and 1000m radii.",
      details: "Evaluates point-pixel class and neighborhood fractions across tree cover, cropland, grassland, and built-up land to establish land context."
    },
    {
      phase: "Phase 6",
      name: "Sentinel-2 Context",
      icon: Satellite,
      color: "text-teal-400 border-teal-200 bg-teal-50",
      summary: "Fetches Copernicus Sentinel-2 L2A optical, NIR, and SWIR spectral surface reflectance.",
      details: "Computes NDVI, NDMI, and NBR spectral indices and evaluates cloud-free coverage within 14-day temporal windows."
    },
    {
      phase: "Phase 7",
      name: "Feature Fusion Engine",
      icon: Layers,
      color: "text-indigo-400 border-indigo-200 bg-indigo-50",
      summary: "Combines 34 multi-source features into a deterministic fusion_v1 vector.",
      details: "Fuses thermal, temporal, industrial, land-cover, and Sentinel spectral signals into a unified, versioned feature profile with explicit coverage tracking."
    },
    {
      phase: "Phase 8 & 9",
      name: "Classification & Explainability",
      icon: BrainCircuit,
      color: "text-violet-400 border-violet-200 bg-violet-50",
      summary: "Classifies thermal archetypes and provides Tree-SHAP feature attributions.",
      details: "Predicts thermal-context archetype using a frozen Random Forest model and extracts exact supporting and opposing feature attributions for model transparency."
    }
  ];

  return (
    <section id="pipeline" className="py-24 bg-white relative overflow-hidden">
      {/* Very faint warm accent area */}
      <div className="absolute top-1/2 left-0 w-72 h-72 bg-orange-50/60 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-700 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>End-to-End Intelligence Pipeline</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight">
            One Pipeline. Fused Evidence.
          </h2>
          <p className="text-neutral-600 text-base leading-relaxed">
            Agnidrishti progressively enriches raw thermal alerts through 8 rigorous geospatial processing phases
            before invoking machine learning.
          </p>
        </div>

        {/* Pipeline Stepper Grid */}
        <div className="grid lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Vertical Pipeline Steps List */}
          <div className="lg:col-span-5 space-y-3">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              const isActive = activeStep === idx;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setActiveStep(idx)}
                  className={`w-full text-left p-4 rounded-xl border transition-all flex items-center justify-between group focus:outline-none focus:ring-2 focus:ring-orange-500 ${
                    isActive
                      ? 'bg-orange-50 border-orange-400 shadow-sm'
                      : 'bg-white border-neutral-200 hover:bg-neutral-50 hover:border-neutral-300'
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <div className={`w-10 h-10 rounded-lg border flex items-center justify-center font-mono ${step.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">{step.phase}</div>
                      <div className={`text-sm font-bold ${isActive ? 'text-neutral-900' : 'text-neutral-700 group-hover:text-neutral-900'}`}>
                        {step.name}
                      </div>
                    </div>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-orange-500 shadow-sm shadow-orange-400' : 'bg-neutral-300'}`} />
                </button>
              );
            })}
          </div>

          {/* Right Column: Step Detail Showcase Card */}
          <div className="lg:col-span-7 sticky top-28">
            <div className="p-8 rounded-2xl bg-white border border-neutral-200 shadow-lg space-y-6">
              <div className="flex items-center justify-between border-b border-neutral-200 pb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-xl border flex items-center justify-center ${steps[activeStep].color}`}>
                    {(() => {
                      const Icon = steps[activeStep].icon;
                      return <Icon className="w-6 h-6" />;
                    })()}
                  </div>
                  <div>
                    <span className="text-xs font-mono text-orange-600 uppercase font-bold tracking-wider">
                      {steps[activeStep].phase} Intelligence Layer
                    </span>
                    <h3 className="text-xl font-extrabold text-neutral-900">{steps[activeStep].name}</h3>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full bg-neutral-100 text-neutral-600 text-xs font-mono border border-neutral-200">
                  Step {activeStep + 1} of 8
                </span>
              </div>

              {/* Summary */}
              <div className="space-y-2">
                <h4 className="text-xs font-mono text-neutral-500 uppercase tracking-wider">Core Objective</h4>
                <p className="text-base text-neutral-800 font-medium leading-relaxed">
                  {steps[activeStep].summary}
                </p>
              </div>

              {/* Details */}
              <div className="space-y-2 pt-2 border-t border-neutral-100">
                <h4 className="text-xs font-mono text-neutral-500 uppercase tracking-wider">Scientific Architecture</h4>
                <p className="text-sm text-neutral-600 leading-relaxed">
                  {steps[activeStep].details}
                </p>
              </div>

              {/* Evidence Flow Integrity Badge */}
              <div className="p-4 rounded-xl bg-neutral-50 border border-neutral-200 flex items-center gap-3 text-xs text-neutral-700">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>
                  Deterministic & Reproducible: Output fed into downstream feature matrix without data manipulation.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
