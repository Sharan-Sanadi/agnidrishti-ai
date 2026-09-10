import { ExternalLink, Database, Globe2, Layers, Satellite } from 'lucide-react';

export function DataSourcesSection() {
  const sources = [
    {
      name: "NASA FIRMS",
      subtitle: "Fire Information for Resource Management System",
      icon: Database,
      badge: "Thermal Source",
      description:
        "Provides near-real-time thermal anomaly detections from NOAA-20 and NOAA-21 VIIRS sensors, including Fire Radiative Power (MW) and acquisition timestamps.",
      url: "https://firms.modaps.eosdis.nasa.gov/",
    },
    {
      name: "OpenStreetMap / Overpass",
      subtitle: "Geospatial Infrastructure Baseline",
      icon: Globe2,
      badge: "Context Source",
      description:
        "Provides global open infrastructure mapping for industrial facilities, power plants, refineries, metal foundries, and industrial zoning boundaries.",
      url: "https://www.openstreetmap.org/",
    },
    {
      name: "ESA WorldCover 2021",
      subtitle: "10 m Global Land Cover",
      icon: Layers,
      badge: "Land-Cover Source",
      description:
        "Delivers an authoritative 10-meter resolution land-cover baseline derived from Sentinel-1 and Sentinel-2, detailing tree cover, cropland, and built-up land.",
      url: "https://esa-worldcover.org/",
    },
    {
      name: "Copernicus Sentinel-2",
      subtitle: "Multi-Spectral Optical Imagery",
      icon: Satellite,
      badge: "Optical Source",
      description:
        "Provides Level-2A surface reflectance across optical, Near-Infrared (NIR), and Short-Wave Infrared (SWIR) bands via the Copernicus Data Space Ecosystem.",
      url: "https://dataspace.copernicus.eu/",
    },
  ];

  return (
    <section className="py-20 bg-neutral-50 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-700 text-xs font-mono">
            <Globe2 className="w-3.5 h-3.5" />
            <span>Authoritative Geospatial Datasets</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-neutral-900 tracking-tight">
            Built on Trusted Earth Observation Data
          </h2>
          <p className="text-neutral-600 text-base leading-relaxed">
            Agnidrishti synthesizes four independent open-data repositories to construct a comprehensive multi-source thermal profile.
          </p>
        </div>

        {/* Sources Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {sources.map((src, idx) => {
            const Icon = src.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-white border border-neutral-200 hover:border-neutral-300 hover:shadow-sm transition-all flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-orange-50 border border-orange-200 text-orange-600 flex items-center justify-center">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-neutral-900">{src.name}</h3>
                        <p className="text-xs text-neutral-500 font-mono">{src.subtitle}</p>
                      </div>
                    </div>
                    <span className="px-2.5 py-1 rounded-full bg-sky-50 text-[10px] font-mono text-sky-700 border border-sky-200">
                      {src.badge}
                    </span>
                  </div>
                  <p className="text-xs text-neutral-700 leading-relaxed">{src.description}</p>
                </div>

                <div className="mt-6 pt-4 border-t border-neutral-200 flex items-center justify-between">
                  <span className="text-[11px] font-mono text-neutral-500">Open Data Provider</span>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs text-orange-600 hover:text-orange-700 font-mono hover:underline focus:outline-none focus:ring-1 focus:ring-orange-500"
                  >
                    <span>Official Portal</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
