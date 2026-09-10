import { AlertTriangle, MapPin, Factory, Trees, Clock } from 'lucide-react';

export function ProblemSection() {
  const problems = [
    {
      icon: MapPin,
      title: "Coordinates Alone Lack Context",
      description:
        "Satellite thermal sensors detect radiative power and latitude/longitude, but cannot tell you what exists at those coordinates or why thermal heat was emitted.",
    },
    {
      icon: Factory,
      title: "Normal Recurrent Industrial Heat",
      description:
        "Refineries, flare stacks, cement kilns, and metal foundries continuously emit intense thermal signatures that trigger satellite alerts during routine operations.",
    },
    {
      icon: Trees,
      title: "Land Cover Dictates Interpretation",
      description:
        "A thermal hotspot in dense forest vs an industrial industrial zone carries vastly different physical implications, requiring an authoritative land-cover baseline.",
    },
    {
      icon: Clock,
      title: "Manual Multi-Source Analysis is Slow",
      description:
        "Manually cross-referencing thermal alerts against historical records, satellite optical passes, and map infrastructure takes hours per incident.",
    },
  ];

  return (
    <section id="overview" className="py-20 bg-neutral-50 border-y border-neutral-200 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200 text-orange-600 text-xs font-mono">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>The Geospatial Intelligence Challenge</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight">
            Why Thermal Detection Alone Isn&apos;t Enough
          </h2>
          <p className="text-neutral-600 text-base leading-relaxed">
            NASA FIRMS tells us <strong className="text-orange-600">WHERE</strong> thermal activity occurs.
            Without multi-source contextual evidence, raw thermal points create false alarms and mask real threats.
          </p>
        </div>

        {/* 4 Problem Cards Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {problems.map((prob, idx) => {
            const Icon = prob.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-white border border-neutral-200 hover:border-neutral-300 hover:shadow-md transition-all shadow-sm flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-orange-50 border border-orange-200 text-orange-600 flex items-center justify-center">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-neutral-900">{prob.title}</h3>
                  <p className="text-xs text-neutral-600 leading-relaxed">{prob.description}</p>
                </div>
                <div className="mt-6 pt-4 border-t border-neutral-100 flex items-center justify-between text-[11px] font-mono text-neutral-400">
                  <span>PROBLEM 0{idx + 1}</span>
                  <span className="text-orange-500 font-bold">Uncontextualized Point</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
