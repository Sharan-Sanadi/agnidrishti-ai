"use client";

import Link from 'next/link';
import { ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

export function Hero() {
  const scrollToPipeline = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const target = document.querySelector('#pipeline');
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section id="top" className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden bg-white">
      {/* Background Ambient Warm Glow — very faint */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] pointer-events-none opacity-60">
        <div className="absolute top-10 left-1/4 w-96 h-96 bg-orange-100/60 rounded-full blur-[128px]" />
        <div className="absolute top-40 right-1/4 w-80 h-80 bg-amber-50/80 rounded-full blur-[100px]" />
      </div>

      {/* Grid Mesh Overlay — near-invisible warm tint */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#f9731608_1px,transparent_1px),linear-gradient(to_bottom,#f9731608_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column: Storytelling & CTAs */}
          <div className="lg:col-span-7 flex flex-col items-start text-left space-y-6">
            {/* SIH Eyebrow Tag */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-orange-50 border border-orange-200 shadow-sm">
              <Sparkles className="w-3.5 h-3.5 text-orange-500" />
              <span className="text-xs font-mono font-medium text-orange-700">
                Smart India Hackathon 2026 • Problem Statement SIH26162
              </span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-neutral-900 tracking-tight leading-[1.1]">
              From Thermal Hotspots to{' '}
              <span className="bg-gradient-to-r from-orange-600 to-amber-500 bg-clip-text text-transparent">
                Explainable Intelligence
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-base sm:text-lg text-neutral-600 font-normal leading-relaxed max-w-2xl">
              AgniDrishti transforms raw NASA FIRMS thermal detections by fusing temporal persistence,
              OpenStreetMap industrial context, 10m ESA WorldCover baseline, and Sentinel-2 spectral evidence
              into model-classified, fully explainable thermal intelligence.
            </p>

            {/* Core Value Statement Badge */}
            <div className="p-3.5 rounded-xl bg-neutral-50 border border-neutral-200 text-xs text-neutral-700 flex items-start gap-3 max-w-xl">
              <div className="p-1 rounded-md bg-orange-100 text-orange-600 shrink-0 mt-0.5">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <strong className="text-neutral-900 font-semibold">Core Scientific Principle:</strong> A satellite thermal detection is not automatically a fire. AgniDrishti resolves context to distinguish industrial, persistent, and environmental thermal behavior.
              </div>
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                href="/dashboard"
                className="group relative inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 text-white font-bold text-sm tracking-wide shadow-xl shadow-orange-950/50 hover:shadow-amber-500/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                <span>Explore Platform</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>

              <a
                href="#pipeline"
                onClick={scrollToPipeline}
                className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-white hover:bg-neutral-50 text-neutral-800 hover:text-neutral-900 font-semibold text-sm border border-neutral-300 transition-all"
              >
                <span>Explore How It Works</span>
              </a>
            </div>

            {/* Data Source Credibility Strip */}
            <div className="pt-6 border-t border-neutral-200 w-full">
              <p className="text-[11px] font-mono text-neutral-500 uppercase tracking-wider mb-3">
                Built on Authoritative Geospatial Data & Science
              </p>
              <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-neutral-700">
                <span className="px-2.5 py-1 rounded-md bg-neutral-100 border border-neutral-200 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                  NASA FIRMS
                </span>
                <span className="px-2.5 py-1 rounded-md bg-neutral-100 border border-neutral-200 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                  PostGIS
                </span>
                <span className="px-2.5 py-1 rounded-md bg-neutral-100 border border-neutral-200 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  ESA WorldCover 2021
                </span>
                <span className="px-2.5 py-1 rounded-md bg-neutral-100 border border-neutral-200 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                  Copernicus Sentinel-2
                </span>
                <span className="px-2.5 py-1 rounded-md bg-neutral-100 border border-neutral-200 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                  Tree-SHAP ML
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Dashboard Mockup — white premium frame */}
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-2xl bg-white border border-neutral-200 p-4 shadow-xl shadow-neutral-200/80">
              {/* Browser/Platform Header */}
              <div className="flex items-center justify-between border-b border-neutral-200 pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-2 text-xs font-mono text-neutral-500">agnidrishti.ai/dashboard</span>
                </div>
                <div className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-mono border border-emerald-200">
                  LIVE POSTGIS FEED
                </div>
              </div>

              {/* Mockup GIS Map View Canvas */}
              <div className="relative h-64 sm:h-72 rounded-xl bg-slate-950 overflow-hidden border border-slate-800 flex flex-col justify-between p-4">
                {/* Mockup Map Canvas Graphics */}
                <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40" />

                {/* Simulated Thermal Observation Point & Multi-layer Radial Rings */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center">
                  <div className="w-48 h-48 rounded-full border border-cyan-500/20 animate-ping absolute opacity-25" />
                  <div className="w-36 h-36 rounded-full border border-purple-500/30 absolute" />
                  <div className="w-24 h-24 rounded-full border border-amber-500/40 bg-amber-500/5 absolute" />
                  <div className="w-6 h-6 rounded-full bg-gradient-to-r from-red-500 to-amber-500 shadow-lg shadow-orange-500/50 flex items-center justify-center animate-pulse">
                    <div className="w-2 h-2 rounded-full bg-white" />
                  </div>
                </div>

                {/* Map Overlay Badges */}
                <div className="relative z-10 flex justify-between items-start">
                  <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 px-3 py-1.5 rounded-lg text-[11px] text-slate-300 font-mono">
                    <span className="text-amber-400 font-bold">Obs ID:</span> firms_30a18cb0
                  </div>
                  <div className="bg-slate-900/90 backdrop-blur-md border border-amber-500/40 px-2.5 py-1 rounded-lg text-[10px] text-amber-300 font-mono font-semibold">
                    FRP: 42.8 MW
                  </div>
                </div>

                {/* Bottom Fused Context Cards Preview */}
                <div className="relative z-10 grid grid-cols-2 gap-2 mt-auto pt-4">
                  <div className="p-2.5 rounded-lg bg-slate-900/95 border border-slate-800 text-[11px]">
                    <div className="text-slate-400 font-mono text-[10px] uppercase">Classification</div>
                    <div className="text-emerald-400 font-bold font-mono">INDUSTRIAL_THERMAL</div>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900/95 border border-slate-800 text-[11px]">
                    <div className="text-slate-400 font-mono text-[10px] uppercase">SHAP Attribution</div>
                    <div className="text-violet-300 font-bold font-mono">+0.384 Persistence</div>
                  </div>
                </div>
              </div>

              {/* Multi-source Context Pipeline Micro-Badges */}
              <div className="mt-4 grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                  <div className="text-amber-400 font-bold">PERSISTENCE</div>
                  <div>84% Recurrent</div>
                </div>
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                  <div className="text-cyan-400 font-bold">OSM PROXIMITY</div>
                  <div>120m Power Plant</div>
                </div>
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                  <div className="text-purple-400 font-bold">SENTINEL-2</div>
                  <div>NDVI 0.12 (Clear)</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
