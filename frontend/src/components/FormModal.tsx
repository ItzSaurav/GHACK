import React, { useState, useEffect } from 'react';
import { FormPreview, FormSubmissionReceipt, Language, SchemeEvaluationResult } from '../types';
import { api } from '../services/api';

interface FormModalProps {
  language: Language;
  scheme: SchemeEvaluationResult;
  sessionId: string;
  onClose: () => void;
}

export const FormModal: React.FC<FormModalProps> = ({
  language,
  scheme,
  sessionId,
  onClose,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<FormPreview | null>(null);
  const [formFields, setFormFields] = useState<Record<string, any>>({});
  const [hasCitizenConsent, setHasCitizenConsent] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [receipt, setReceipt] = useState<FormSubmissionReceipt | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadPreview() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getFormPreview(sessionId, scheme.scheme_id);
        if (isMounted) {
          setPreview(data);
          const initialValues: Record<string, any> = {};
          data.fields.forEach((f) => {
            initialValues[f.field_key] = f.value ?? '';
          });
          setFormFields(initialValues);
          setLoading(false);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to load form preview.');
          setLoading(false);
        }
      }
    }
    loadPreview();
    return () => {
      isMounted = false;
    };
  }, [sessionId, scheme.scheme_id]);

  const handleInputChange = (key: string, value: any) => {
    setFormFields((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasCitizenConsent || !preview) return;

    try {
      setIsSubmitting(true);
      setError(null);
      const res = await api.submitForm(
        preview.form_id,
        scheme.scheme_id,
        hasCitizenConsent,
        formFields,
        language
      );
      setReceipt(res);
      setIsSubmitting(false);
    } catch (err: any) {
      setError(err.message || 'Submission failed.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="form-modal-title">
      <div className="modal-window">
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-titles">
            <h2 id="form-modal-title">
              {language === 'hi' ? 'फॉर्म सहायता एवं पूर्व-समीक्षा' : 'Form Assistance & Citizen Review'}
            </h2>
            <p className="modal-scheme-name">{scheme.scheme_name}</p>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close Modal"
          >
            ×
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {loading && (
            <div className="loading-spinner-box">
              <div className="spinner"></div>
              <p>{language === 'hi' ? 'फॉर्म विवरण लोड हो रहा है...' : 'Loading form preview...'}</p>
            </div>
          )}

          {error && (
            <div className="alert-banner alert-danger" role="alert">
              <p>{error}</p>
            </div>
          )}

          {/* Submission Receipt View */}
          {receipt ? (
            <div className="receipt-view">
              <div className="receipt-badge">
                {language === 'hi' ? 'सफलतापूर्वक दर्ज किया गया' : 'Recorded Successfully'}
              </div>
              <h3>{receipt.message}</h3>

              <div className="receipt-details-table">
                <div className="receipt-row">
                  <span className="receipt-label">{language === 'hi' ? 'आवेदन ट्रैकिंग संख्या:' : 'Application Tracking ID:'}</span>
                  <span className="receipt-code">{receipt.tracking_id}</span>
                </div>
                <div className="receipt-row">
                  <span className="receipt-label">{language === 'hi' ? 'योजना:' : 'Scheme:'}</span>
                  <span>{scheme.scheme_name}</span>
                </div>
                <div className="receipt-row">
                  <span className="receipt-label">{language === 'hi' ? 'स्थिति:' : 'Status:'}</span>
                  <span className="badge badge-success">{receipt.status}</span>
                </div>
              </div>

              <div className="receipt-next-steps">
                <h4>{language === 'hi' ? 'आगे की प्रक्रिया:' : 'Next Steps:'}</h4>
                <ul>
                  {receipt.next_steps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              </div>

              <div className="receipt-actions">
                <button type="button" className="btn btn-primary" onClick={onClose}>
                  {language === 'hi' ? 'पूर्ण करें' : 'Done'}
                </button>
              </div>
            </div>
          ) : (
            preview && (
              <form onSubmit={handleSubmit} className="form-preview-form">
                {/* Security & Privacy Notice */}
                <div className="privacy-callout">
                  <span className="callout-title">
                    {language === 'hi' ? 'गोपनीयता एवं सुरक्षा नियम:' : 'Privacy & Safety Guarantee:'}
                  </span>
                  <p>
                    {language === 'hi'
                      ? 'नागरिक की स्पष्ट अनुमति के बिना कोई भी फॉर्म जमा नहीं होता। इस सिस्टम में कभी भी आधार नंबर, बैंक पासवर्ड या ओटीपी दर्ज न करें।'
                      : 'No form is submitted without explicit citizen consent. Never enter sensitive identity numbers, passwords, or OTPs into this assistant.'}
                  </p>
                </div>

                <div className="form-fields-grid">
                  {preview.fields.map((field) => (
                    <div key={field.field_key} className="form-field-group">
                      <label htmlFor={`field-${field.field_key}`}>
                        {language === 'hi' ? field.label_hi : field.label_en}
                      </label>

                      {field.field_type === 'boolean' ? (
                        <select
                          id={`field-${field.field_key}`}
                          className="form-control"
                          value={
                            formFields[field.field_key] === true
                              ? 'true'
                              : formFields[field.field_key] === false
                              ? 'false'
                              : ''
                          }
                          onChange={(e) =>
                            handleInputChange(
                              field.field_key,
                              e.target.value === '' ? null : e.target.value === 'true'
                            )
                          }
                        >
                          <option value="">{language === 'hi' ? '-- चयन करें --' : '-- Select --'}</option>
                          <option value="true">{language === 'hi' ? 'हाँ (Yes)' : 'Yes'}</option>
                          <option value="false">{language === 'hi' ? 'नहीं (No)' : 'No'}</option>
                        </select>
                      ) : (
                        <input
                          id={`field-${field.field_key}`}
                          type={field.field_type === 'number' ? 'number' : 'text'}
                          className="form-control"
                          value={formFields[field.field_key] ?? ''}
                          onChange={(e) => handleInputChange(field.field_key, e.target.value)}
                          placeholder={language === 'hi' ? 'जानकारी दर्ज करें' : 'Enter detail'}
                        />
                      )}
                    </div>
                  ))}
                </div>

                {/* Explicit Citizen Consent Gate */}
                <div className="consent-gate-box">
                  <label className="consent-checkbox-label">
                    <input
                      type="checkbox"
                      checked={hasCitizenConsent}
                      onChange={(e) => setHasCitizenConsent(e.target.checked)}
                      required
                    />
                    <span className="consent-text">
                      {language === 'hi'
                        ? 'मैंने उपरोक्त सभी जानकारी को स्वयं पढ़ / सुनकर जांच लिया है और मैं इसकी सत्यता की पुष्टि करता हूँ।'
                        : 'I have personally reviewed and confirmed all prefilled information for submission.'}
                    </span>
                  </label>
                </div>

                {/* Form Buttons */}
                <div className="modal-footer-actions">
                  <button
                    type="submit"
                    className="btn btn-primary btn-submit-form"
                    disabled={!hasCitizenConsent || isSubmitting}
                  >
                    {isSubmitting
                      ? (language === 'hi' ? 'जमा हो रहा है...' : 'Submitting...')
                      : (language === 'hi' ? 'सत्यापन हेतु दर्ज करें' : 'Submit for Verification')}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={onClose}
                    disabled={isSubmitting}
                  >
                    {language === 'hi' ? 'रद्द करें' : 'Cancel'}
                  </button>
                </div>
              </form>
            )
          )}
        </div>
      </div>
    </div>
  );
};
