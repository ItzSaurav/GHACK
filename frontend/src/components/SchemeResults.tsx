import React, { useState } from 'react';
import { Language, SchemeEvaluationResult } from '../types';

interface SchemeResultsProps {
  language: Language;
  results: SchemeEvaluationResult[];
  onStartFormAssistance: (scheme: SchemeEvaluationResult) => void;
}

export const SchemeResults: React.FC<SchemeResultsProps> = ({
  language,
  results,
  onStartFormAssistance,
}) => {
  const [expandedSchemeId, setExpandedSchemeId] = useState<string | null>(null);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'potential_match':
        return (
          <span className="status-badge badge-success">
            {language === 'gu'
              ? 'પાત્ર (Potential Match)'
              : language === 'hi'
              ? 'पात्र (Potential Match)'
              : 'Potential Match'}
          </span>
        );
      case 'manual_review':
        return (
          <span className="status-badge badge-warning">
            {language === 'gu'
              ? 'સમીક્ષા જરૂરી (Review Needed)'
              : language === 'hi'
              ? 'समीक्षा आवश्यक (Review Needed)'
              : 'Manual Review'}
          </span>
        );
      case 'insufficient_information':
        return (
          <span className="status-badge badge-info">
            {language === 'gu'
              ? 'અધૂરી માહિતી'
              : language === 'hi'
              ? 'अधूरी जानकारी'
              : 'Missing Info'}
          </span>
        );
      case 'not_matched':
      default:
        return (
          <span className="status-badge badge-neutral">
            {language === 'gu'
              ? 'અપાત્ર (Not Matched)'
              : language === 'hi'
              ? 'अपात्र (Not Matched)'
              : 'Not Matched'}
          </span>
        );
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedSchemeId(expandedSchemeId === id ? null : id);
  };

  if (!results || results.length === 0) {
    return null;
  }

  const matchedList = results.filter((r) => r.status === 'potential_match' || r.status === 'manual_review');
  const otherList = results.filter((r) => r.status !== 'potential_match' && r.status !== 'manual_review');

  return (
    <div className="scheme-results-container" role="region" aria-label="Scheme Results">
      <div className="results-banner">
        <h2>
          {language === 'gu'
            ? 'યોજના પાત્રતા પરિણામો'
            : language === 'hi'
            ? 'योजना पात्रता परिणाम'
            : 'Scheme Eligibility Evaluation'}
        </h2>
        <p className="results-subtitle">
          {language === 'gu'
            ? 'નીચે આપેલા પરિણામો સત્તાવાર સરકારી નિયમોના આધારે નક્કી કરવામાં આવ્યા છે.'
            : language === 'hi'
            ? 'नीचे दिए गए परिणाम आधिकारिक नियमों के आधार पर निकाले गए हैं।'
            : 'Evaluation based on deterministic government rules and your stated facts.'}
        </p>
      </div>

      {/* Primary Matches */}
      {matchedList.length > 0 && (
        <div className="scheme-cards-list">
          {matchedList.map((scheme) => {
            const isCentral = scheme.scheme_id.startsWith('central_') || (!scheme.scheme_id.includes('state_') && !scheme.scheme_id.includes('karnataka'));
            return (
              <div key={scheme.scheme_id} className="scheme-card scheme-matched">
                <div className="card-top-meta" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <span className={`scope-badge ${isCentral ? 'badge-central' : 'badge-state'}`}>
                    {isCentral ? 'Central Scheme' : 'State Scheme'}
                  </span>
                  {getStatusBadge(scheme.status)}
                </div>

                <div className="scheme-card-header" style={{ marginBottom: '0.25rem' }}>
                  <div className="scheme-meta">
                    <h3 className="scheme-title">{scheme.scheme_name}</h3>
                    <p className="scheme-dept">{scheme.department}</p>
                  </div>
                </div>

                {/* Verified Match Pill */}
                <div style={{ backgroundColor: 'var(--surface-canvas)', border: '1px solid var(--border-subtle)', padding: '0.2rem 0.5rem', borderRadius: '6px', display: 'inline-flex', alignItems: 'center', gap: '0.35rem', margin: '0.25rem 0 0.5rem', fontSize: '0.75rem', color: 'var(--secondary)' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--secondary)' }}>verified</span>
                  <span>
                    {scheme.reasons && scheme.reasons[0]
                      ? scheme.reasons[0]
                      : language === 'gu'
                      ? 'સત્યાપિત નિયમ મેળ'
                      : language === 'hi'
                      ? 'सत्यापित नियम मिलान'
                      : 'Rule-based Match'}
                  </span>
                </div>

                {/* Benefit Box */}
                <div className="benefit-highlight-box">
                  <span className="benefit-label">
                    {language === 'gu' ? 'મુખ્ય લાભ:' : language === 'hi' ? 'मुख्य लाभ:' : 'Key Benefit:'}
                  </span>
                  <p className="benefit-text">{scheme.benefit_summary}</p>
                </div>

                {/* Accordion Toggle */}
                <div className="scheme-details-toggle">
                  <button
                    type="button"
                    className="accordion-btn"
                    onClick={() => toggleExpand(scheme.scheme_id)}
                  >
                    {expandedSchemeId === scheme.scheme_id
                      ? language === 'gu'
                        ? 'ઓછી વિગત જુઓ'
                        : language === 'hi'
                        ? 'कम विवरण देखें'
                        : 'Hide Details'
                      : language === 'gu'
                      ? 'કારણો અને જરૂરી દસ્તાવેજો જુઓ'
                      : language === 'hi'
                      ? 'कारण एवं आवश्यक दस्तावेज देखें'
                      : 'View Reasons & Required Documents'}
                  </button>
                </div>

                {/* Expanded details */}
                {expandedSchemeId === scheme.scheme_id && (
                  <div className="scheme-expanded-content">
                    {/* Evaluated Reasons */}
                    <div className="detail-section">
                      <h4>
                        {language === 'gu'
                          ? 'પાત્રતાના કારણો:'
                          : language === 'hi'
                          ? 'पात्रता के कारण:'
                          : 'Eligibility Reasons:'}
                      </h4>
                      <ul className="reasons-list">
                        {scheme.reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Required Documents */}
                    <div className="detail-section">
                      <h4>
                        {language === 'gu'
                          ? 'જરૂરી દસ્તાવેજો (Checklist):'
                          : language === 'hi'
                          ? 'आवश्यक दस्तावेज (Checklist):'
                          : 'Required Documents Checklist:'}
                      </h4>
                      <ul className="documents-checklist">
                        {scheme.required_documents.map((doc, i) => (
                          <li key={i}>
                            <label className="checkbox-label">
                              <input type="checkbox" defaultChecked={false} />
                              <span>{doc}</span>
                            </label>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Metadata & Source Link */}
                    <div className="scheme-footer-meta">
                      <p>
                        {language === 'gu' ? 'નિયમ આવૃત્તિ:' : language === 'hi' ? 'नियम संस्करण:' : 'Rule Version:'}{' '}
                        {scheme.rule_version} |{' '}
                        {language === 'gu' ? 'ચકાસાયેલ તારીખ:' : language === 'hi' ? 'सत्यापित तिथि:' : 'Verified:'}{' '}
                        {scheme.last_verified_date}
                      </p>
                      <a
                        href={scheme.official_source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="official-portal-link"
                      >
                        {language === 'gu'
                          ? 'સત્તાવાર સરકારી પોર્ટલ ખોલો'
                          : language === 'hi'
                          ? 'आधिकारिक सरकारी पोर्टल खोलें'
                          : 'Official Government Portal'}
                      </a>
                    </div>
                  </div>
                )}

                {/* Form Assistance Call to Action */}
                <div className="scheme-card-actions">
                  <button
                    type="button"
                    className="btn btn-action"
                    onClick={() => onStartFormAssistance(scheme)}
                  >
                    {language === 'gu'
                      ? 'ફોર્મ ભરવામાં મદદ મેળવો'
                      : language === 'hi'
                      ? 'फॉर्म भरने में सहायता लें'
                      : 'Get Form Assistance'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Non-Matching / Incomplete schemes */}
      {otherList.length > 0 && (
        <details className="other-schemes-accordion">
          <summary className="other-schemes-summary">
            {language === 'gu'
              ? `અન્ય યોજનાઓ (${otherList.length}) - જે હાલમાં મેળ ખાતી નથી`
              : language === 'hi'
              ? `अन्य योजनाएं (${otherList.length}) - जो वर्तमान में मेल नहीं खातीं`
              : `Other Schemes (${otherList.length}) - Not currently matched`}
          </summary>
          <div className="other-schemes-list">
            {otherList.map((scheme) => (
              <div key={scheme.scheme_id} className="scheme-card-compact">
                <div className="compact-header">
                  <h4>{scheme.scheme_name}</h4>
                  {getStatusBadge(scheme.status)}
                </div>
                <ul className="compact-reasons">
                  {scheme.reasons.slice(0, 2).map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Honest Uncertainty Disclaimer */}
      <div className="disclaimer-footer">
        <p>
          <strong>
            {language === 'gu' ? 'મહત્વપૂર્ણ સૂચના:' : language === 'hi' ? 'महत्वपूर्ण सूचना:' : 'Important Notice:'}
          </strong>{' '}
          {language === 'gu'
            ? 'આ સહાયક માત્ર માહિતી માર્ગદર્શન પૂરું પાડે છે. અંતિમ પાત્રતા સત્તાવાર સરકારી ચકાસણી પર આધારિત છે. અમારા કેટેલોગમાં નામ ન હોવાનો અર્થ એ નથી કે તમે અન્ય કોઈ સરકારી કલ્યાણકારી યોજના માટે અપાત્ર છો.'
            : language === 'hi'
            ? 'यह सहायक केवल सूचनात्मक मार्गदर्शन प्रदान करता है। अंतिम पात्रता आधिकारिक सरकारी सत्यापन पर निर्भर करती है। हमारे कैटलॉग में नाम न होने का अर्थ यह नहीं है कि आप किसी अन्य सरकारी योजना के पात्र नहीं हैं।'
            : 'This assistant provides informational matching only. Final eligibility is determined by the administering government department upon official verification. Lack of match in this catalogue does not mean universal ineligibility for welfare.'}
        </p>
      </div>
    </div>
  );
};
