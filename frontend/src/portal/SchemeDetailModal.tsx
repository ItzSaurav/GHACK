import React from 'react';

interface SchemeDetailModalProps {
  scheme: any;
  onClose: () => void;
  onAskAssistant: (scheme: any) => void;
}

export const SchemeDetailModal: React.FC<SchemeDetailModalProps> = ({
  scheme,
  onClose,
  onAskAssistant,
}) => {
  if (!scheme) return null;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="scheme-detail-title"
    >
      <div className="modal-window scheme-detail-modal">
        {/* Header */}
        <div className="modal-header">
          <div className="modal-titles">
            <span className="badge badge-info">
              {scheme.is_illustrative ? 'Illustrative Demo Scheme' : 'Verified Government Program'}
            </span>
            <h2 id="scheme-detail-title">{scheme.name}</h2>
            {scheme.name_hi && <p className="scheme-title-hi">{scheme.name_hi}</p>}
            <p className="modal-scheme-dept">{scheme.department}</p>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close details modal"
          >
            ×
          </button>
        </div>

        {/* Content Body */}
        <div className="modal-body scheme-detail-body">
          {/* Overview */}
          <div className="detail-section">
            <h3>Description & Purpose</h3>
            <p>{scheme.description}</p>
            {scheme.description_hi && <p className="text-muted-hi">{scheme.description_hi}</p>}
          </div>

          {/* Benefit summary */}
          <div className="benefit-highlight-box">
            <span className="benefit-label">Assistance & Benefit Summary:</span>
            <p className="benefit-text">{scheme.benefit_summary}</p>
          </div>

          {/* Geographic Applicability */}
          <div className="detail-section">
            <h4>Applicable Geography</h4>
            <p>
              <strong>{scheme.state_applicability || 'All India'}</strong>
            </p>
          </div>

          {/* Verified Criteria */}
          {scheme.criteria && scheme.criteria.length > 0 && (
            <div className="detail-section">
              <h4>Eligibility Screening Criteria</h4>
              <ul className="criteria-table-list">
                {scheme.criteria.map((crit: any) => (
                  <li key={crit.id} className="crit-item">
                    <span className="crit-desc">{crit.description}</span>
                    {crit.is_exclusion && (
                      <span className="badge badge-warning">Exclusion Criterion</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Required Documents */}
          {scheme.required_documents && scheme.required_documents.length > 0 && (
            <div className="detail-section">
              <h4>Required Documents Checklist</h4>
              <ul className="documents-checklist">
                {scheme.required_documents.map((doc: string, idx: number) => (
                  <li key={idx}>
                    <label className="checkbox-label">
                      <input type="checkbox" defaultChecked={false} />
                      <span>{doc}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Provenance & Official Source */}
          <div className="detail-section metadata-section">
            <h4>Official Authority & Verification</h4>
            <p className="meta-text">
              Rule Version: <strong>{scheme.rule_version}</strong> | Data Version:{' '}
              <strong>{scheme.scheme_version}</strong> | Last Verified:{' '}
              <strong>{scheme.last_verified_date}</strong>
            </p>

            {scheme.official_source_url && (
              <a
                href={scheme.official_source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="official-portal-link"
              >
                Visit Official Government Portal
              </a>
            )}
          </div>
        </div>

        {/* Modal Actions */}
        <div className="modal-footer-actions">
          <button
            type="button"
            className="btn btn-hero-assistant"
            onClick={() => onAskAssistant(scheme)}
          >
            Ask Sahaay Assistant About This Scheme
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
