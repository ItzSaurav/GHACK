import React from 'react';

export const PortalFooter: React.FC = () => {
  return (
    <footer id="footer-section" className="portal-footer">
      <div className="portal-container footer-content-grid">
        {/* Col 1: About */}
        <div className="footer-col" id="about-section">
          <div className="footer-brand">
            <span className="brand-name">Sahaay</span>
            <span className="brand-tagline">Public Welfare Discovery Portal</span>
          </div>
          <p className="footer-desc">
            Sahaay is an engineering prototype demonstrating multilingual, voice-first
            access to public welfare schemes for low-literacy citizens. It integrates
            deterministic rule matching with step-by-step form assistance.
          </p>
        </div>

        {/* Col 2: Accessibility */}
        <div className="footer-col">
          <h4 className="footer-heading">Accessibility Standards</h4>
          <ul className="footer-links-list">
            <li>WCAG 2.2 compliant high-contrast color palette</li>
            <li>Full keyboard navigation and focus indicators</li>
            <li>Voice-first input via Web Speech API in Hindi and English</li>
            <li>One-question-at-a-time conversational interface</li>
            <li>Text fallback for noisy environments</li>
          </ul>
        </div>

        {/* Col 3: Privacy and Trust */}
        <div className="footer-col">
          <h4 className="footer-heading">Privacy & Safety</h4>
          <ul className="footer-links-list">
            <li>Zero collection or retention of Aadhaar numbers or passwords</li>
            <li>Pre-submission review gate requiring citizen explicit consent</li>
            <li>Transparent eligibility explanations with official source citations</li>
            <li>Sanitized server logs redacting potential identifiers</li>
          </ul>
        </div>

        {/* Col 4: Important Official Disclaimer */}
        <div className="footer-col footer-disclaimer-col">
          <h4 className="footer-heading">Demonstration Notice</h4>
          <p className="footer-disclaimer-text">
            This website is a demonstration project created for research and prototyping
            purposes. It is not affiliated with, authorized by, or endorsed by the Government
            of India or any State Government. To apply officially, always consult designated
            administrative authorities or official portals.
          </p>
        </div>
      </div>

      <div className="footer-bottom-bar">
        <div className="portal-container bottom-bar-inner">
          <p>© 2026 Sahaay Prototype. Open public-interest engineering architecture.</p>
          <p className="footer-status-pill">System Status: Active</p>
        </div>
      </div>
    </footer>
  );
};
