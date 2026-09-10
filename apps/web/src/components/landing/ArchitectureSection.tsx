import { Cpu, Server, Database, BrainCircuit, Code, Terminal, Box } from 'lucide-react';

export function ArchitectureSection() {
  const techStack = [
    {
      category: "Frontend Web App",
      icon: Code,
      color: "border-cyan-200 text-cyan-400 bg-cyan-50",
      items: ["Next.js 16 (App Router)", "React 19 & TypeScript", "Tailwind CSS 4", "Lucide Icons"],
    },
    {
      category: "Backend API Service",
      icon: Server,
      color: "border-amber-200 text-amber-400 bg-amber-50",
      items: ["Python 3.11", "FastAPI (Async NRT)", "Pydantic V2 Schemas", "Uvicorn & UV Package Manager"],
    },
    {
      category: "Geospatial Storage",
      icon: Database,
      color: "border-blue-200 text-blue-400 bg-blue-50",
      items: ["PostgreSQL 16", "PostGIS 3.4 (SRID 4326)", "SQLAlchemy 2.0 Async", "Alembic Migrations"],
    },
    {
      category: "ML & Explainability",
      icon: BrainCircuit,
      color: "border-violet-200 text-violet-400 bg-violet-50",
      items: ["scikit-learn (RandomForest)", "Tree-SHAP Attributions", "Joblib Model Persistence", "Feature Fusion Matrix (fusion_v1)"],
    },
    {
      category: "Geospatial GIS Engine",
      icon: Box,
      color: "border-emerald-200 text-emerald-400 bg-emerald-50",
      items: ["Leaflet & React-Leaflet", "Rasterio Tile Sampling", "Shapely Geometry Operations", "PyProj Projections"],
    },
    {
      category: "Containerization",
      icon: Terminal,
      color: "border-teal-200 text-teal-400 bg-teal-50",
      items: ["Docker & Docker Compose", "PostGIS Official Image", "Development & Prod Containers", "Environment Validation"],
    },
  ];

  return (
    <section id="technology" className="py-24 bg-white relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono">
            <Cpu className="w-3.5 h-3.5" />
            <span>Technical Architecture</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight">
            Production-Grade Full-Stack Stack
          </h2>
          <p className="text-neutral-600 text-base leading-relaxed">
            Agnidrishti is engineered with modern, high-performance open-source frameworks for sub-second spatial querying and machine learning inference.
          </p>
        </div>

        {/* Tech Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {techStack.map((tech, idx) => {
            const Icon = tech.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-white border border-neutral-200 hover:border-neutral-300 hover:shadow-sm transition-all flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${tech.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-bold text-neutral-900">{tech.category}</h3>
                  </div>

                  <ul className="space-y-2 pt-2 border-t border-neutral-100">
                    {tech.items.map((item, itemIdx) => (
                      <li key={itemIdx} className="flex items-center gap-2 text-xs text-neutral-700 font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
