import { ShieldCheck, Info, Check } from 'lucide-react';

export function ScientificIntegritySection() {
  const boundaries = [
    {
      title: "Satellite Thermal Hotspot ≠ Confirmed Physical Fire",
      description:
        "NASA FIRMS VIIRS detects mid-wave and long-wave infrared radiance exceeding background thresholds. This includes routine industrial flare stacks, power plant cooling outlets, metal processing, and agricultural burns alongside wildland vegetation fires.",
    },
    {
      title: "ML Context Archetype ≠ Physical Causality Confirmation",
      description:
        "The Phase-8 machine learning pipeline classifies thermal-context archetypes based on multi-source feature signatures. It provides reproducible decision-support intelligence without claiming unverified physical causality on the ground.",
    },
    {
      title: "Model Explainability (Tree-SHAP) ≠ Incident Investigation Report",
      description:
        "Phase-9 Tree-SHAP attributions quantify the exact mathematical contribution of each contextual feature toward the model's internal prediction, ensuring complete transparency into how the model reached its output.",
    },
  ];

  return (
    <section id="research" className="py-20 bg-stone-50 border-y border-neutral-200 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Scientific Rigor & Claim Safeguards</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight">
            Designed for Evidence, Not Overclaiming
          </h2>
          <p className="text-neutral-600 text-base leading-relaxed">
            AgniDrishti maintains strict scientific boundaries between satellite observations, feature extraction, model inference, and ground reality.
          </p>
        </div>

        {/* 3 Boundary Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {boundaries.map((bound, idx) => (
            <div
              key={idx}
              className="p-6 rounded-2xl bg-white border border-neutral-200 shadow-sm space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center font-mono font-bold text-sm">
                  0{idx + 1}
                </div>
                <h3 className="text-base font-bold text-neutral-900 leading-snug">{bound.title}</h3>
                <p className="text-xs text-neutral-600 leading-relaxed">{bound.description}</p>
              </div>
              <div className="pt-3 border-t border-neutral-100 flex items-center gap-2 text-[11px] font-mono text-emerald-700">
                <Check className="w-3.5 h-3.5" />
                <span>Verified Scientific Boundary</span>
              </div>
            </div>
          ))}
        </div>

        {/* Official Decision-Support Notice Banner */}
        <div className="mt-12 p-5 rounded-2xl bg-amber-50 border border-amber-200 flex items-start gap-4 text-xs text-neutral-700">
          <div className="p-2 rounded-lg bg-amber-100 text-amber-700 border border-amber-300 shrink-0 mt-0.5">
            <Info className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h4 className="font-bold text-neutral-900 text-sm">Decision-Support Platform Disclaimer</h4>
            <p className="text-neutral-700 leading-relaxed">
              AgniDrishti provides decision-support geospatial intelligence for industrial monitoring and environmental assessment.
              Model predictions and Tree-SHAP attributions support analyst investigations and do not replace formal ground verification or statutory emergency authority dispatches.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
