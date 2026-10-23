import React from 'react';

interface CategoryCardsProps {
  selectedCategory: string | null;
  onSelectCategory: (category: string | null) => void;
}

interface CategoryItem {
  id: string;
  title: string;
  titleHi: string;
  desc: string;
  schemeCount: number;
}

const CATEGORIES: CategoryItem[] = [
  {
    id: 'agriculture',
    title: 'Agriculture & Farmers',
    titleHi: 'कृषि एवं किसान कल्याण',
    desc: 'Income support, crop calamity relief, fertilizer subsidy, and farmer welfare.',
    schemeCount: 2,
  },
  {
    id: 'healthcare',
    title: 'Healthcare & Wellness',
    titleHi: 'स्वास्थ्य एवं परिवार कल्याण',
    desc: 'Cashless hospitalization cover, maternity nutrition, and elderly medical assurance.',
    schemeCount: 2,
  },
  {
    id: 'social_welfare',
    title: 'Social Welfare & Pension',
    titleHi: 'सामाजिक सुरक्षा एवं पेंशन',
    desc: 'Old age security, unorganized worker pension, and disability assistance.',
    schemeCount: 1,
  },
  {
    id: 'education',
    title: 'Education & Scholarships',
    titleHi: 'शिक्षा एवं छात्रवृत्ति',
    desc: 'Pre-matric, post-matric, higher education fellowships, and vocational stipends.',
    schemeCount: 0,
  },
  {
    id: 'housing',
    title: 'Housing & Shelter',
    titleHi: 'आवास एवं ग्रामीण विकास',
    desc: 'Affordable pucca housing construction subsidies for rural and urban poor.',
    schemeCount: 0,
  },
  {
    id: 'employment',
    title: 'Employment & Skills',
    titleHi: 'रोजगार एवं कौशल विकास',
    desc: 'Rural employment guarantees (MGNREGA), skill development, and apprenticeships.',
    schemeCount: 0,
  },
  {
    id: 'financial',
    title: 'Financial Assistance',
    titleHi: 'वित्तीय समावेशन एवं ऋण',
    desc: 'Jan Dhan accounts, micro-credit, collateral-free mudra loans, and DBT benefits.',
    schemeCount: 0,
  },
  {
    id: 'business',
    title: 'Business & Self-Employment',
    titleHi: 'उद्योग एवं स्वरोजगार',
    desc: 'Support for street vendors, artisan toolkits, and micro-enterprise development.',
    schemeCount: 0,
  },
];

export const CategoryCards: React.FC<CategoryCardsProps> = ({
  selectedCategory,
  onSelectCategory,
}) => {
  return (
    <section id="categories-section" className="categories-section">
      <div className="portal-container">
        <div className="section-header">
          <span className="section-eyebrow">BROWSE BY DOMAIN</span>
          <h2 className="section-title">Government Scheme Categories</h2>
          <p className="section-desc">
            Explore welfare programs categorized by sector and beneficiary focus.
          </p>
        </div>

        <div className="categories-grid">
          {CATEGORIES.map((cat) => {
            const isSelected = selectedCategory === cat.id;
            return (
              <div
                key={cat.id}
                className={`category-card ${isSelected ? 'category-active' : ''}`}
                onClick={() => onSelectCategory(isSelected ? null : cat.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    onSelectCategory(isSelected ? null : cat.id);
                  }
                }}
                aria-pressed={isSelected}
              >
                <div className="category-header">
                  <div className="category-icon-box">
                    <span className="category-icon-text">{cat.title.slice(0, 2).toUpperCase()}</span>
                  </div>
                  <span className="category-count-badge">
                    {cat.schemeCount > 0 ? `${cat.schemeCount} verified` : 'Cataloguing'}
                  </span>
                </div>

                <h3 className="category-title">{cat.title}</h3>
                <p className="category-title-hi">{cat.titleHi}</p>
                <p className="category-desc">{cat.desc}</p>

                <div className="category-footer">
                  <span className="category-link-text">
                    {isSelected ? 'Clear Filter' : 'Explore Category'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
