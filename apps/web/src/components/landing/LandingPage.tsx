"use client";

import { Navbar } from './Navbar';
import { Hero } from './Hero';
import { ProblemSection } from './ProblemSection';
import { PipelineSection } from './PipelineSection';
import { CapabilitiesSection } from './CapabilitiesSection';
import { PlatformPreviewSection } from './PlatformPreviewSection';
import { DataSourcesSection } from './DataSourcesSection';
import { ArchitectureSection } from './ArchitectureSection';
import { ScientificIntegritySection } from './ScientificIntegritySection';
import { FinalCTA } from './FinalCTA';
import { Footer } from './Footer';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-neutral-900 font-sans selection:bg-amber-500 selection:text-black">
      <Navbar />
      <main>
        <Hero />
        <ProblemSection />
        <PipelineSection />
        <CapabilitiesSection />
        <PlatformPreviewSection />
        <DataSourcesSection />
        <ArchitectureSection />
        <ScientificIntegritySection />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
