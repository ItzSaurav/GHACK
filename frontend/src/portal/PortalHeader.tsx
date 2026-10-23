import React, { useState } from 'react';

interface PortalHeaderProps {
  onOpenAssistant: () => void;
  onNavigateSection: (sectionId: string) => void;
  activeSection: string;
}

export const PortalHeader: React.FC<PortalHeaderProps> = ({
  onOpenAssistant,
  onNavigateSection,
  activeSection,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNavClick = (sectionId: string) => {
    onNavigateSection(sectionId);
    setMobileMenuOpen(false);
  };

  const handleFontSize = (size: 'small' | 'normal' | 'large') => {
    if (size === 'large') {
      document.documentElement.style.fontSize = '112%';
    } else if (size === 'small') {
      document.documentElement.style.fontSize = '92%';
    } else {
      document.documentElement.style.fontSize = '100%';
    }
  };

  return (
    <header className="portal-header">
      {/* TOP BANNER: Prototype Disclaimer (from reference) */}
      <div className="top-prototype-disclaimer">
        <span className="prototype-pill">PROTOTYPE DEMONSTRATION</span>
        <span className="prototype-text">
          Sahaay is an independent civic research concept — not an official government agency. Information for illustrative discovery only.
        </span>
      </div>

      {/* Main Navigation Bar */}
      <div className="portal-main-nav">
        <div className="portal-container nav-content">
          {/* Brand */}
          <div className="portal-brand" onClick={() => handleNavClick('hero-section')}>
            <div className="brand-logo-mark" aria-hidden="true">
              <span className="material-symbols-outlined">account_balance</span>
            </div>
            <div className="brand-text">
              <div className="brand-title-row">
                <span className="brand-name">Sahaay</span>
                <span className="brand-tagline">| Scheme Directory</span>
              </div>
              <span className="brand-sub">A demonstration portal for public welfare information</span>
            </div>
          </div>

          {/* Desktop Nav Links */}
          <nav className="desktop-nav" aria-label="Portal Navigation">
            <button
              type="button"
              className={`nav-link ${activeSection === 'hero-section' ? 'active' : ''}`}
              onClick={() => handleNavClick('hero-section')}
            >
              Home
            </button>
            <button
              type="button"
              className={`nav-link ${activeSection === 'discovery-section' ? 'active' : ''}`}
              onClick={() => handleNavClick('discovery-section')}
            >
              Find Schemes
            </button>
            <button
              type="button"
              className={`nav-link ${activeSection === 'categories-section' ? 'active' : ''}`}
              onClick={() => handleNavClick('categories-section')}
            >
              Categories
            </button>
            <button
              type="button"
              className={`nav-link ${activeSection === 'listings-section' ? 'active' : ''}`}
              onClick={() => handleNavClick('listings-section')}
            >
              All Schemes
            </button>
            <button
              type="button"
              className={`nav-link ${activeSection === 'about-section' ? 'active' : ''}`}
              onClick={() => handleNavClick('about-section')}
            >
              About
            </button>
          </nav>

          {/* Action CTAs */}
          <div className="nav-actions">
            {/* Font scaling controls */}
            <div className="font-scale-controls" title="Adjust text size">
              <button
                type="button"
                className="font-btn"
                onClick={() => handleFontSize('small')}
                aria-label="Decrease font size"
              >
                A-
              </button>
              <button
                type="button"
                className="font-btn"
                onClick={() => handleFontSize('normal')}
                aria-label="Normal font size"
              >
                A
              </button>
              <button
                type="button"
                className="font-btn"
                onClick={() => handleFontSize('large')}
                aria-label="Increase font size"
              >
                A+
              </button>
            </div>

            <button
              type="button"
              className="btn btn-assistant-nav"
              onClick={onOpenAssistant}
              aria-label="Open voice assistant"
            >
              <span className="assistant-dot" aria-hidden="true"></span>
              <span>Voice Assistant</span>
            </button>

            {/* Mobile Menu Toggle */}
            <button
              type="button"
              className="mobile-menu-toggle"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-label="Toggle navigation menu"
            >
              <span className="menu-bar"></span>
              <span className="menu-bar"></span>
              <span className="menu-bar"></span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <nav className="mobile-nav-drawer" aria-label="Mobile Navigation">
            <button
              type="button"
              className="mobile-nav-link"
              onClick={() => handleNavClick('hero-section')}
            >
              Home
            </button>
            <button
              type="button"
              className="mobile-nav-link"
              onClick={() => handleNavClick('discovery-section')}
            >
              Find Schemes (6 Steps)
            </button>
            <button
              type="button"
              className="mobile-nav-link"
              onClick={() => handleNavClick('categories-section')}
            >
              Scheme Categories
            </button>
            <button
              type="button"
              className="mobile-nav-link"
              onClick={() => handleNavClick('listings-section')}
            >
              Browse All Schemes
            </button>
            <button
              type="button"
              className="mobile-nav-link"
              onClick={() => handleNavClick('about-section')}
            >
              About This Demo
            </button>
            <button
              type="button"
              className="mobile-nav-link mobile-nav-assistant"
              onClick={() => {
                onOpenAssistant();
                setMobileMenuOpen(false);
              }}
            >
              Open Voice Assistant
            </button>
          </nav>
        )}
      </div>
    </header>
  );
};
