import React, { useState, useMemo } from 'react';

interface SchemeListingsProps {
  schemes: any[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedCategory: string | null;
  onSelectCategory: (cat: string | null) => void;
  onViewDetails: (scheme: any) => void;
  onAskAssistant: (scheme: any) => void;
  loading: boolean;
  error: string | null;
}

export const SchemeListings: React.FC<SchemeListingsProps> = ({
  schemes,
  searchQuery,
  onSearchChange,
  selectedCategory,
  onSelectCategory,
  onViewDetails,
  onAskAssistant,
  loading,
  error,
}) => {
  const [scopeFilter, setScopeFilter] = useState<'all' | 'central' | 'state'>('all');
  const [stateFilter, setStateFilter] = useState<string>('all');

  const filteredSchemes = useMemo(() => {
    return schemes.filter((s) => {
      // 1. Text search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = s.name.toLowerCase().includes(q) || (s.name_hi && s.name_hi.toLowerCase().includes(q));
        const matchesDept = s.department.toLowerCase().includes(q);
        const matchesDesc = s.description.toLowerCase().includes(q);
        if (!matchesName && !matchesDept && !matchesDesc) return false;
      }

      // 2. Scope filter (central vs state)
      if (scopeFilter === 'central') {
        if (s.state_applicability !== 'All India') return false;
      } else if (scopeFilter === 'state') {
        if (s.state_applicability === 'All India') return false;
      }

      // 3. Category filter
      if (selectedCategory) {
        const idLower = s.id.toLowerCase();
        const nameLower = s.name.toLowerCase();
        if (
          selectedCategory === 'agriculture' &&
          !idLower.includes('kisan') &&
          !idLower.includes('kss') &&
          !nameLower.includes('kisan')
        ) {
          return false;
        }
        if (
          selectedCategory === 'healthcare' &&
          !idLower.includes('pmjay') &&
          !idLower.includes('pmmvy') &&
          !nameLower.includes('arogya')
        ) {
          return false;
        }
        if (
          selectedCategory === 'social_welfare' &&
          !idLower.includes('sym') &&
          !nameLower.includes('maan-dhan')
        ) {
          return false;
        }
      }

      // 4. State filter
      if (stateFilter !== 'all') {
        if (s.state_applicability !== 'All India' && !s.state_applicability.toLowerCase().includes(stateFilter.toLowerCase())) {
          return false;
        }
      }

      return true;
    });
  }, [schemes, searchQuery, scopeFilter, selectedCategory, stateFilter]);

  return (
    <section id="listings-section" className="listings-section">
      <div className="portal-container">
        <div className="section-header">
          <span className="section-eyebrow">CATALOGUE DIRECTORY</span>
          <h2 className="section-title">Government Schemes Directory</h2>
          <p className="section-desc">
            Search and filter through active welfare programs from Central ministries and State departments.
          </p>
        </div>

        {/* Filter Controls Bar */}
        <div className="filter-controls-bar">
          <div className="search-filter-box">
            <input
              type="text"
              className="filter-search-input"
              placeholder="Filter by keyword (e.g. Kisan, Shram, Health)..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              aria-label="Filter schemes by keyword"
            />
            {searchQuery && (
              <button
                type="button"
                className="clear-search-btn"
                onClick={() => onSearchChange('')}
              >
                Clear
              </button>
            )}
          </div>

          <div className="pill-filters-group">
            <button
              type="button"
              className={`filter-pill ${scopeFilter === 'all' ? 'pill-active' : ''}`}
              onClick={() => setScopeFilter('all')}
            >
              All Programs
            </button>
            <button
              type="button"
              className={`filter-pill ${scopeFilter === 'central' ? 'pill-active' : ''}`}
              onClick={() => setScopeFilter('central')}
            >
              Central Schemes
            </button>
            <button
              type="button"
              className={`filter-pill ${scopeFilter === 'state' ? 'pill-active' : ''}`}
              onClick={() => setScopeFilter('state')}
            >
              State Schemes
            </button>
          </div>

          {selectedCategory && (
            <div className="active-category-indicator">
              <span>Category: <strong>{selectedCategory.replace('_', ' ').toUpperCase()}</strong></span>
              <button
                type="button"
                className="category-clear-btn"
                onClick={() => onSelectCategory(null)}
              >
                × Remove filter
              </button>
            </div>
          )}
        </div>

        {/* Loading and Error states */}
        {loading && (
          <div className="loading-spinner-box">
            <div className="spinner"></div>
            <p>Loading scheme directory from verified repository...</p>
          </div>
        )}

        {error && (
          <div className="alert-banner alert-warning" role="alert">
            <p>Could not reach live backend: {error}. Showing offline cached directory records.</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredSchemes.length === 0 && (
          <div className="empty-state-box">
            <div className="empty-icon-graphic">0</div>
            <h3>No Schemes Match Your Selected Filters</h3>
            <p>
              Try clearing your search query or selecting "All Programs" to view the complete catalogue.
            </p>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                onSearchChange('');
                setScopeFilter('all');
                onSelectCategory(null);
                setStateFilter('all');
              }}
            >
              Reset All Filters
            </button>
          </div>
        )}

        {/* Listings Grid */}
        <div className="scheme-grid">
          {filteredSchemes.map((scheme) => (
            <div key={scheme.id} className="portal-scheme-card">
              <div className="card-top-meta">
                <span className={`scope-badge ${scheme.state_applicability === 'All India' ? 'badge-central' : 'badge-state'}`}>
                  {scheme.state_applicability === 'All India' ? 'Central Government' : 'State Initiative'}
                </span>
                {scheme.is_illustrative && (
                  <span className="badge badge-warning">Demo Model</span>
                )}
              </div>

              <h3 className="card-scheme-title">{scheme.name}</h3>
              {scheme.name_hi && <p className="card-title-hi">{scheme.name_hi}</p>}

              <p className="card-dept-name">{scheme.department}</p>
              <p className="card-desc-snippet">{scheme.description}</p>

              <div className="card-benefit-row">
                <span className="benefit-badge-pill">Benefit</span>
                <span className="benefit-brief-text">{scheme.benefit_summary}</span>
              </div>

              <div className="card-action-footer">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => onViewDetails(scheme)}
                >
                  View Details
                </button>
                <button
                  type="button"
                  className="btn btn-assistant-small"
                  onClick={() => onAskAssistant(scheme)}
                >
                  Ask Assistant
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
