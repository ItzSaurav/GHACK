import React, { useState } from 'react';

interface HeroSectionProps {
  onSearch: (query: string) => void;
  onStartDiscovery: () => void;
  onBrowseAll: () => void;
  onOpenAssistant: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onSearch,
  onStartDiscovery,
  onBrowseAll,
  onOpenAssistant,
}) => {
  const [searchInput, setSearchInput] = useState('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchInput.trim());
  };

  return (
    <section id="hero-section" className="portal-hero">
      <div className="portal-container hero-container">
        <div className="hero-content">
          <div className="hero-tag">
            <span>PUBLIC WELFARE DISCOVERY PLATFORM</span>
          </div>

          <h1 className="hero-title">
            Find Government Schemes That May Be Right for You
          </h1>

          <p className="hero-subtitle">
            Discover Central and State welfare assistance programs through structured
            eligibility rules, clear document checklists, and multilingual voice assistance.
          </p>

          {/* Prominent Search Bar */}
          <form className="hero-search-form" onSubmit={handleSearchSubmit}>
            <div className="search-input-wrapper">
              <input
                type="text"
                className="hero-search-input"
                placeholder="Search schemes by name, keyword, or occupation (e.g. Kisan, Pension, Health, Student)..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                aria-label="Search government schemes"
              />
              <button type="submit" className="hero-search-btn">
                Search
              </button>
            </div>
          </form>

          {/* Action CTAs */}
          <div className="hero-ctas">
            <button
              type="button"
              className="btn btn-hero-primary"
              onClick={onStartDiscovery}
            >
              Find Schemes for Me (6 Steps)
            </button>

            <button
              type="button"
              className="btn btn-hero-secondary"
              onClick={onBrowseAll}
            >
              Browse All Schemes
            </button>

            <button
              type="button"
              className="btn btn-hero-assistant"
              onClick={onOpenAssistant}
            >
              <span className="mic-dot" aria-hidden="true"></span>
              Speak with Sahaay Assistant
            </button>
          </div>

          <div className="hero-disclaimer-note">
            <span>Note: This is an informational demonstration portal. Scheme matching does not guarantee eligibility or official government sanction.</span>
          </div>
        </div>
      </div>
    </section>
  );
};
