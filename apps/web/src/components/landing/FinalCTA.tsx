import Link from 'next/link';
import { ArrowRight, Flame, Layers } from 'lucide-react';

export function FinalCTA() {
  const scrollToPipeline = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const target = document.querySelector('#pipeline');
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="py-20 bg-neutral-50 relative overflow-hidden">
      {/* Very faint warm radial glow on light background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,#f9731608,transparent_100%)] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="rounded-3xl bg-white border border-neutral-200 p-8 sm:p-14 text-center space-y-8 shadow-lg relative overflow-hidden">
          {/* Flame Icon Badge */}
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 p-0.5 shadow-lg shadow-orange-200 flex items-center justify-center">
            <div className="w-full h-full bg-white rounded-[14px] flex items-center justify-center">
              <Flame className="w-8 h-8 text-orange-500" />
            </div>
          </div>

          {/* Call to Action Text */}
          <div className="max-w-2xl mx-auto space-y-4">
            <h2 className="text-3xl sm:text-4xl font-black text-neutral-900 tracking-tight">
              Explore Thermal Intelligence in Context
            </h2>
            <p className="text-neutral-600 text-base leading-relaxed">
              Inspect real multi-source thermal observations through the Agnidrishti geospatial platform with interactive persistence, land-cover, Sentinel-2, classification, and Tree-SHAP explainability.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Link
              href="/dashboard"
              className="group relative inline-flex items-center gap-2.5 px-7 py-4 rounded-xl bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 text-white font-bold text-sm tracking-wide shadow-2xl shadow-orange-950/60 hover:shadow-amber-500/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              <span>Explore Platform</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>

            <a
              href="#pipeline"
              onClick={scrollToPipeline}
              className="inline-flex items-center gap-2 px-6 py-4 rounded-xl bg-white hover:bg-neutral-50 text-neutral-800 hover:text-neutral-900 font-semibold text-sm border border-neutral-300 transition-all"
            >
              <Layers className="w-4 h-4 text-orange-500" />
              <span>View Pipeline</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
