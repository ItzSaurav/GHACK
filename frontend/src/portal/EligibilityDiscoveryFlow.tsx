import React, { useState } from 'react';
import { CitizenFacts } from '../types';

interface EligibilityDiscoveryFlowProps {
  onCompleteDiscovery: (facts: CitizenFacts) => void;
  onOpenAssistantWithFacts: (facts: CitizenFacts) => void;
}

const INDIAN_STATES = [
  'All India',
  'Andhra Pradesh',
  'Bihar',
  'Delhi',
  'Gujarat',
  'Haryana',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Tamil Nadu',
  'Telangana',
  'Uttar Pradesh',
  'West Bengal',
];

export const EligibilityDiscoveryFlow: React.FC<EligibilityDiscoveryFlowProps> = ({
  onCompleteDiscovery,
  onOpenAssistantWithFacts,
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [facts, setFacts] = useState<CitizenFacts>({
    state_of_residence: 'All India',
    age: 30,
    gender: 'female',
    social_category: 'general',
    occupation: 'farmer',
    annual_income: 120000,
    monthly_income: 10000,
    owns_cultivable_land: true,
    is_income_tax_payer: false,
    covered_by_epfo_esic: false,
    has_crop_loss: false,
    is_pregnant_or_lactating: false,
  });

  const handleNext = () => {
    if (currentStep < 6) {
      setCurrentStep(currentStep + 1);
    } else {
      onCompleteDiscovery(facts);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const updateFact = (key: keyof CitizenFacts, value: any) => {
    setFacts((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <section id="discovery-section" className="discovery-section">
      <div className="portal-container">
        <div className="section-header">
          <span className="section-eyebrow">STEP-BY-STEP SCREENING</span>
          <h2 className="section-title">Eligibility Discovery in 6 Simple Steps</h2>
          <p className="section-desc">
            Filter schemes based on your profile. Step through each question or skip
            to check which programs may match your household.
          </p>
        </div>

        {/* Step Indicator Progress Bar */}
        <div className="steps-progress-bar" role="progressbar" aria-valuenow={currentStep} aria-valuemin={1} aria-valuemax={6}>
          <div className="steps-progress-track">
            <div
              className="steps-progress-fill"
              style={{ width: `${((currentStep - 1) / 5) * 100}%` }}
            ></div>
          </div>
          <div className="steps-markers">
            {[1, 2, 3, 4, 5, 6].map((stepNum) => (
              <button
                key={stepNum}
                type="button"
                className={`step-marker ${stepNum === currentStep ? 'step-active' : stepNum < currentStep ? 'step-completed' : ''}`}
                onClick={() => setCurrentStep(stepNum)}
                aria-label={`Go to step ${stepNum}`}
              >
                {stepNum}
              </button>
            ))}
          </div>
        </div>

        {/* Step Container Card */}
        <div className="step-card">
          {/* Step 1: State / UT */}
          {currentStep === 1 && (
            <div className="step-content">
              <span className="step-number-tag">Step 1 of 6</span>
              <h3 className="step-heading">Select Your State or Union Territory</h3>
              <p className="step-instruction">
                Welfare programs can be applicable across India or targeted to specific state residents.
              </p>
              <div className="step-form-group">
                <label htmlFor="state-select">State / Union Territory:</label>
                <select
                  id="state-select"
                  className="step-select"
                  value={facts.state_of_residence || 'All India'}
                  onChange={(e) => updateFact('state_of_residence', e.target.value)}
                >
                  {INDIAN_STATES.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Step 2: Age */}
          {currentStep === 2 && (
            <div className="step-content">
              <span className="step-number-tag">Step 2 of 6</span>
              <h3 className="step-heading">Choose Your Age Range</h3>
              <p className="step-instruction">
                Different welfare programs are designed for youth, working age citizens, or senior citizens (70+).
              </p>
              <div className="step-options-grid">
                {[
                  { label: 'Under 18 years (Minor / Student)', age: 16 },
                  { label: '18 to 40 years (Young adult / PM-SYM pension bracket)', age: 28 },
                  { label: '41 to 59 years (Mature adult / Working citizen)', age: 48 },
                  { label: '60 to 69 years (Senior Citizen)', age: 64 },
                  { label: '70 years and above (Ayushman Bharat universal cover)', age: 72 },
                ].map((opt, i) => (
                  <button
                    key={i}
                    type="button"
                    className={`step-choice-btn ${facts.age === opt.age ? 'selected' : ''}`}
                    onClick={() => updateFact('age', opt.age)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: Gender & Special Conditions */}
          {currentStep === 3 && (
            <div className="step-content">
              <span className="step-number-tag">Step 3 of 6</span>
              <h3 className="step-heading">Select Gender and Applicant Details</h3>
              <p className="step-instruction">
                Maternity and specialized welfare incentives (such as PMMVY) have specific gender eligibility.
              </p>
              <div className="step-form-group">
                <label>Gender:</label>
                <div className="step-options-grid">
                  {['female', 'male', 'other'].map((g) => (
                    <button
                      key={g}
                      type="button"
                      className={`step-choice-btn ${facts.gender === g ? 'selected' : ''}`}
                      onClick={() => updateFact('gender', g)}
                    >
                      {g === 'female' ? 'Female (महिला)' : g === 'male' ? 'Male (पुरुष)' : 'Other (अन्य)'}
                    </button>
                  ))}
                </div>
              </div>

              {facts.gender === 'female' && (
                <div className="step-form-group" style={{ marginTop: '1rem' }}>
                  <label>Are you currently pregnant or a lactating mother?</label>
                  <div className="step-options-grid">
                    <button
                      type="button"
                      className={`step-choice-btn ${facts.is_pregnant_or_lactating === true ? 'selected' : ''}`}
                      onClick={() => updateFact('is_pregnant_or_lactating', true)}
                    >
                      Yes, pregnant / lactating mother
                    </button>
                    <button
                      type="button"
                      className={`step-choice-btn ${facts.is_pregnant_or_lactating === false ? 'selected' : ''}`}
                      onClick={() => updateFact('is_pregnant_or_lactating', false)}
                    >
                      No
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 4: Occupation */}
          {currentStep === 4 && (
            <div className="step-content">
              <span className="step-number-tag">Step 4 of 6</span>
              <h3 className="step-heading">Select Employment or Occupation</h3>
              <p className="step-instruction">
                Choose the category that best matches your primary source of livelihood.
              </p>
              <div className="step-options-grid">
                {[
                  { label: 'Farmer / Agricultural Cultivator', val: 'farmer' },
                  { label: 'Unorganized Sector / Daily Wage Worker', val: 'unorganized_worker' },
                  { label: 'Small Business / Self-Employed', val: 'self_employed' },
                  { label: 'Private Sector Salaried Employee', val: 'salaried_private' },
                  { label: 'Government / Public Sector Employee', val: 'salaried_govt' },
                  { label: 'Homemaker / Household Care', val: 'homemaker' },
                ].map((occ) => (
                  <button
                    key={occ.val}
                    type="button"
                    className={`step-choice-btn ${facts.occupation === occ.val ? 'selected' : ''}`}
                    onClick={() => updateFact('occupation', occ.val)}
                  >
                    {occ.label}
                  </button>
                ))}
              </div>

              {facts.occupation === 'farmer' && (
                <div className="step-form-group" style={{ marginTop: '1.25rem' }}>
                  <label>Does your family own cultivable land?</label>
                  <div className="step-options-grid">
                    <button
                      type="button"
                      className={`step-choice-btn ${facts.owns_cultivable_land === true ? 'selected' : ''}`}
                      onClick={() => updateFact('owns_cultivable_land', true)}
                    >
                      Yes, own cultivable land
                    </button>
                    <button
                      type="button"
                      className={`step-choice-btn ${facts.owns_cultivable_land === false ? 'selected' : ''}`}
                      onClick={() => updateFact('owns_cultivable_land', false)}
                    >
                      No, landless
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 5: Income & Exclusions */}
          {currentStep === 5 && (
            <div className="step-content">
              <span className="step-number-tag">Step 5 of 6</span>
              <h3 className="step-heading">Select Income and Tax Status</h3>
              <p className="step-instruction">
                Welfare schemes have income ceilings and statutory exclusion criteria.
              </p>

              <div className="step-form-group">
                <label>Annual Family Income Range:</label>
                <div className="step-options-grid">
                  {[
                    { label: 'Below ₹1,00,000 / year (Under ₹8,000/month)', annual: 80000, monthly: 6500 },
                    { label: '₹1,00,000 to ₹1,80,000 / year (₹15,000/month ceiling)', annual: 150000, monthly: 12500 },
                    { label: '₹1,80,000 to ₹2,50,000 / year', annual: 220000, monthly: 18000 },
                    { label: 'Above ₹2,50,000 / year', annual: 400000, monthly: 33000 },
                  ].map((inc, i) => (
                    <button
                      key={i}
                      type="button"
                      className={`step-choice-btn ${facts.annual_income === inc.annual ? 'selected' : ''}`}
                      onClick={() => {
                        updateFact('annual_income', inc.annual);
                        updateFact('monthly_income', inc.monthly);
                      }}
                    >
                      {inc.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="step-form-group" style={{ marginTop: '1.25rem' }}>
                <label>Do you or your household pay income tax?</label>
                <div className="step-options-grid">
                  <button
                    type="button"
                    className={`step-choice-btn ${facts.is_income_tax_payer === false ? 'selected' : ''}`}
                    onClick={() => updateFact('is_income_tax_payer', false)}
                  >
                    No, do not pay income tax
                  </button>
                  <button
                    type="button"
                    className={`step-choice-btn ${facts.is_income_tax_payer === true ? 'selected' : ''}`}
                    onClick={() => updateFact('is_income_tax_payer', true)}
                  >
                    Yes, income tax payer
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Step 6: Confirmation & Review */}
          {currentStep === 6 && (
            <div className="step-content">
              <span className="step-number-tag">Step 6 of 6</span>
              <h3 className="step-heading">Profile Summary & Scheme Discovery</h3>
              <p className="step-instruction">
                Review your profile answers before screening against verified scheme criteria.
              </p>

              <div className="summary-facts-box">
                <div className="summary-fact-row">
                  <span className="summary-key">State:</span>
                  <span className="summary-val">{facts.state_of_residence || 'All India'}</span>
                </div>
                <div className="summary-fact-row">
                  <span className="summary-key">Age:</span>
                  <span className="summary-val">{facts.age ?? 'Not specified'} years</span>
                </div>
                <div className="summary-fact-row">
                  <span className="summary-key">Gender:</span>
                  <span className="summary-val">{facts.gender || 'Not specified'}</span>
                </div>
                <div className="summary-fact-row">
                  <span className="summary-key">Occupation:</span>
                  <span className="summary-val">{facts.occupation || 'Not specified'}</span>
                </div>
                <div className="summary-fact-row">
                  <span className="summary-key">Income Tax Payer:</span>
                  <span className="summary-val">{facts.is_income_tax_payer ? 'Yes' : 'No'}</span>
                </div>
              </div>

              <div className="step-dual-action-box">
                <button
                  type="button"
                  className="btn btn-hero-primary"
                  onClick={() => onCompleteDiscovery(facts)}
                >
                  View Matched Schemes on Portal
                </button>
                <button
                  type="button"
                  className="btn btn-hero-assistant"
                  onClick={() => onOpenAssistantWithFacts(facts)}
                >
                  Ask Voice Assistant to Verify
                </button>
              </div>
            </div>
          )}

          {/* Navigation Controls */}
          <div className="step-card-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleBack}
              disabled={currentStep === 1}
            >
              Previous Step
            </button>

            {currentStep < 6 && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleNext}
              >
                Next Step
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
