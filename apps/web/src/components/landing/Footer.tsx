"use client";

import Link from 'next/link';
import { Flame } from 'lucide-react';

export function Footer() {
  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <footer className="bg-white border-t border-neutral-200 py-12 text-neutral-500 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          {/* Brand & Identity */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-md">
              <Flame className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-neutral-900 text-sm tracking-tight font-mono">
                AGNIDRISHTI <span className="text-orange-600">AI</span>
              </span>
              <span className="text-[11px] text-neutral-500 font-mono">
                Smart India Hackathon 2026 • SIH26162
              </span>
            </div>
          </div>

          {/* Nav Links */}
          <div className="flex flex-wrap items-center gap-6 font-mono text-[11px]">
            <a href="#overview" onClick={(e) => scrollToSection(e, '#overview')} className="hover:text-neutral-900 transition-colors">
              Overview
            </a>
            <a href="#pipeline" onClick={(e) => scrollToSection(e, '#pipeline')} className="hover:text-neutral-900 transition-colors">
              Pipeline
            </a>
            <a href="#capabilities" onClick={(e) => scrollToSection(e, '#capabilities')} className="hover:text-neutral-900 transition-colors">
              Capabilities
            </a>
            <a href="#technology" onClick={(e) => scrollToSection(e, '#technology')} className="hover:text-neutral-900 transition-colors">
              Technology
            </a>
            <a href="#research" onClick={(e) => scrollToSection(e, '#research')} className="hover:text-neutral-900 transition-colors">
              Research
            </a>
            <Link href="/dashboard" className="text-orange-600 hover:text-orange-700 font-bold">
              Open Dashboard →
            </Link>
          </div>
        </div>

        {/* Data Source Acknowledgements & Copyright */}
        <div className="pt-6 border-t border-neutral-100 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-neutral-500">
          <p>
            Powered by open geospatial data from NASA FIRMS, OpenStreetMap, ESA WorldCover 2021, and Copernicus Sentinel-2.
          </p>
          <p className="font-mono">
            © 2026 Agnidrishti AI. SIH Problem Statement SIH26162.
          </p>
        </div>
      </div>
    </footer>
  );
}
