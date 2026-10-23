import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SchemeListings } from './SchemeListings';
import { SchemeDetailModal } from './SchemeDetailModal';

interface HostPortalProps {
  onOpenAssistant: (initialPrompt?: string) => void;
}

export const HostPortal: React.FC<HostPortalProps> = ({ onOpenAssistant }) => {
  const [schemes, setSchemes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchCategory, setSearchCategory] = useState('All Categories');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [activeModalScheme, setActiveModalScheme] = useState<any | null>(null);

  // 6-Step Scheme Finder State
  const [selectedGender, setSelectedGender] = useState<'male' | 'female' | 'transgender' | null>('male');
  const [selectedAge, setSelectedAge] = useState<string>('25');
  const [wizardStep, setWizardStep] = useState<number>(1);

  useEffect(() => {
    let isMounted = true;
    async function loadCatalogue() {
      try {
        setLoading(true);
        const data = await api.listSchemes();
        if (isMounted) {
          setSchemes(data);
          setLoading(false);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Could not fetch schemes from backend');
          setLoading(false);
        }
      }
    }
    loadCatalogue();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleGlobalSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchCategory === 'Schemes' || searchCategory === 'All Categories') {
      const el = document.getElementById('schemes-catalogue-section');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const handleCategoryCardClick = (catKey: string) => {
    setSelectedCategory(catKey);
    const el = document.getElementById('schemes-catalogue-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleNextWizardStep = () => {
    if (wizardStep < 6) {
      setWizardStep((prev) => prev + 1);
    }
    // Launch assistant with the user's entered gender & age
    const genderLabel = selectedGender ? (selectedGender === 'male' ? 'male' : selectedGender === 'female' ? 'female' : 'transgender') : '';
    const ageLabel = selectedAge ? `${selectedAge} years old` : '';
    const prompt = `I am a ${ageLabel} ${genderLabel} citizen. Help me discover government welfare schemes I qualify for.`.trim();
    onOpenAssistant(prompt);
  };

  const handleResetForm = () => {
    setSelectedGender(null);
    setSelectedAge('');
    setWizardStep(1);
    setSelectedCategory(null);
    setSearchQuery('');
  };

  const handleAskAssistantAboutScheme = (scheme: any) => {
    setActiveModalScheme(null);
    onOpenAssistant(`Tell me about eligibility rules and benefits for ${scheme.name}`);
  };

  return (
    <div className="bg-[#f4f6f9] text-gray-800 font-sans antialiased relative min-h-screen flex flex-col justify-between">
      {/* BEGIN: TopBarAndNavigation */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-xs">
        {/* Top Utility & Main Header Row */}
        <div className="max-w-[1536px] mx-auto px-4 lg:px-8 py-3 flex items-center justify-between gap-4">
          {/* Left: Emblem & Portal Name */}
          <div className="flex items-center gap-3 shrink-0" data-purpose="branding">
            {/* Lion Capital Ashoka Emblem Replica */}
            <svg aria-hidden="true" className="h-14 w-auto text-[#0c2340]" fill="currentColor" viewBox="0 0 100 130">
              <path d="M50 5C45 5 40 8 38 12C36 10 33 8 28 8C20 8 16 15 16 23C16 33 22 41 29 44C27 48 24 53 24 60C24 72 33 81 44 83V92H25C23 92 21 94 21 96C21 98 23 100 25 100H44V108H20C18 108 17 110 17 112C17 114 18 116 20 116H80C82 116 83 114 83 112C83 110 82 108 80 108H56V100H75C77 100 79 98 79 96C79 94 77 92 75 92H56V83C67 81 76 72 76 60C76 53 73 48 71 44C78 41 84 33 84 23C84 15 80 8 72 8C67 8 64 10 62 12C60 8 55 5 50 5ZM50 15C53 15 56 18 56 22C56 26 53 29 50 29C47 29 44 26 44 22C44 18 47 15 50 15ZM30 20C33 20 36 23 36 27C36 31 33 34 30 34C27 34 24 31 24 27C24 23 27 20 30 20ZM70 20C73 20 76 23 76 27C76 31 73 34 70 34C67 34 64 31 64 27C64 23 67 20 70 20ZM50 36C59 36 67 44 67 55C67 66 59 74 50 74C41 74 33 66 33 55C33 44 41 36 50 36Z" />
            </svg>
            <div className="leading-tight">
              <div className="text-[28px] font-extrabold tracking-tight text-[#0c2340] flex items-baseline">
                <span>india</span>
                <span className="text-[#0c2340]">.gov.</span>
                <span className="text-govRed">in</span>
              </div>
              <p className="text-[12px] uppercase tracking-wider text-gray-600 font-semibold">National Portal of India</p>
            </div>
          </div>

          {/* Center-Right: Search Input with Select and Action Button */}
          <div className="flex-1 max-w-2xl mx-6 hidden md:block" data-purpose="global-search">
            <form onSubmit={handleGlobalSearch} className="flex items-center border border-gray-300 rounded-md overflow-hidden bg-white shadow-inner focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
              <div className="pl-3.5 pr-2 text-gray-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <input
                className="w-full py-2.5 px-2 text-sm text-gray-800 placeholder-gray-400 border-0 focus:ring-0 outline-none"
                placeholder="Search schemes by name, keyword, or occupation..."
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <div className="relative border-l border-gray-200">
                <select
                  className="py-2.5 pl-3 pr-8 text-sm text-gray-700 bg-transparent border-0 focus:ring-0 cursor-pointer outline-none"
                  value={searchCategory}
                  onChange={(e) => setSearchCategory(e.target.value)}
                >
                  <option>All Categories</option>
                  <option>Schemes</option>
                  <option>Services</option>
                  <option>Documents</option>
                  <option>Forms</option>
                </select>
              </div>
              <button
                className="bg-[#e12b38] hover:bg-red-700 text-white font-medium text-sm px-6 py-2.5 transition-colors duration-150 ease-in-out cursor-pointer"
                type="submit"
              >
                Search
              </button>
            </form>
          </div>

          {/* Far Right: Accessibility & Internationalization Utility Tools */}
          <div className="flex items-center space-x-3 text-sm text-gray-700 font-medium shrink-0" data-purpose="utility-nav">
            <a className="hover:text-blue-700 hidden xl:inline-block text-xs border-r pr-3 border-gray-300" href="#main-content">
              Skip to main content
            </a>
            {/* Calendar Icon */}
            <button className="p-1 hover:text-blue-700 text-gray-600" title="Calendar and Schedules">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
                <rect height="18" rx="2" ry="2" width="18" x="3" y="4" />
                <line x1="16" x2="16" y1="2" y2="6" />
                <line x1="8" x2="8" y1="2" y2="6" />
                <line x1="3" x2="21" y1="10" y2="10" />
                <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01" />
              </svg>
            </button>
            <span className="text-gray-300">|</span>
            {/* Accessibility Icon */}
            <button className="p-1 hover:text-blue-700 text-gray-600" title="Accessibility Options">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9.5" />
                <circle cx="12" cy="7" r="1.5" />
                <path d="M7 11h10M12 11v8M9 19l3-4 3 4" />
              </svg>
            </button>
            <span className="text-gray-300">|</span>
            {/* Language Switcher */}
            <button
              className="font-bold px-1 hover:text-blue-700 text-gray-800 text-sm flex items-center space-x-0.5"
              title="Switch Language"
              onClick={() => onOpenAssistant()}
            >
              <span>अ</span>
              <span className="text-xs text-gray-400">|</span>
              <span>A</span>
            </button>
            <span className="text-gray-300">|</span>
            {/* Indian National Flag */}
            <div className="flex flex-col w-6 h-4 border border-gray-300 rounded-[2px] overflow-hidden shadow-xs cursor-pointer" title="Republic of India">
              <div className="h-1/3 bg-[#FF9933]"></div>
              <div className="h-1/3 bg-white flex items-center justify-center relative">
                <div className="w-1.5 h-1.5 rounded-full border border-blue-900 bg-blue-900"></div>
              </div>
              <div className="h-1/3 bg-[#138808]"></div>
            </div>
          </div>
        </div>

        {/* Secondary Navigation Menu Bar */}
        <nav className="max-w-[1536px] mx-auto px-4 lg:px-8 border-t border-gray-100 flex items-center justify-between text-sm font-semibold text-gray-700">
          <ul className="flex items-center space-x-8">
            <li>
              <a className="inline-block py-3 hover:text-govRed transition-colors" href="#main-content">
                Acts & Rules
              </a>
            </li>
            <li className="relative">
              <a className="inline-block py-3 text-govNavy font-bold border-b-2 border-govRed -mb-px" href="#schemes-catalogue-section">
                Schemes
              </a>
            </li>
            <li>
              <a className="inline-block py-3 hover:text-govRed transition-colors" href="#main-content">
                Constitution of India
              </a>
            </li>
            <li>
              <a className="inline-block py-3 hover:text-govRed transition-colors" href="#main-content">
                Documents
              </a>
            </li>
          </ul>
          {/* Voice Assistant Direct Header Button */}
          <button
            type="button"
            onClick={() => onOpenAssistant()}
            className="flex items-center gap-1.5 py-1 px-3 bg-red-50 text-govRed rounded-full border border-red-200 text-xs font-bold hover:bg-red-100 transition-colors"
          >
            <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
            Voice Assistant
          </button>
        </nav>
      </header>
      {/* END: TopBarAndNavigation */}

      {/* BEGIN: MainContent */}
      <main className="relative overflow-hidden flex-1 pb-16" id="main-content">
        {/* Background Framing Cutouts */}
        <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden select-none">
          {/* Left side citizen artwork card */}
          <div className="absolute -left-6 top-8 w-72 lg:w-96 h-[460px] opacity-90 hidden sm:block">
            <div className="w-full h-full rounded-3xl overflow-hidden shadow-sm bg-gradient-to-tr from-amber-100 via-orange-50 to-emerald-50 relative border-r border-b border-gray-200 hero-mask-left">
              <svg className="w-full h-full text-amber-600/20" fill="currentColor" viewBox="0 0 200 300">
                <circle cx="100" cy="80" r="40" />
                <path d="M40 180 C40 130 160 130 160 180 L170 300 L30 300 Z" />
              </svg>
              <div className="absolute bottom-6 left-6 right-6 p-4 bg-white/80 backdrop-blur-xs rounded-xl shadow-xs text-xs text-gray-700">
                <span className="font-bold text-govNavy block">Empowering Rural India</span>
                Financial security & agricultural subsidies
              </div>
            </div>
          </div>
          {/* Right side family with mobile device artwork card */}
          <div className="absolute -right-6 top-8 w-72 lg:w-96 h-[460px] opacity-90 hidden sm:block">
            <div className="w-full h-full rounded-3xl overflow-hidden shadow-sm bg-gradient-to-tl from-blue-100 via-sky-50 to-indigo-50 relative border-l border-b border-gray-200 hero-mask-right">
              <svg className="w-full h-full text-blue-600/20" fill="currentColor" viewBox="0 0 200 300">
                <circle cx="70" cy="70" r="30" />
                <circle cx="130" cy="65" r="25" />
                <path d="M20 180 C20 120 180 120 180 180 L190 300 L10 300 Z" />
              </svg>
              <div className="absolute bottom-6 left-6 right-6 p-4 bg-white/80 backdrop-blur-xs rounded-xl shadow-xs text-xs text-gray-700">
                <span className="font-bold text-govNavy block">Digital Inclusion</span>
                Direct Benefit Transfer (DBT) anytime, anywhere
              </div>
            </div>
          </div>
        </div>

        {/* Central Wrapper */}
        <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
          {/* Breadcrumb */}
          <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-xs sm:text-sm text-gray-500 mb-4">
            <a className="hover:text-blue-800" href="#main-content">
              Home
            </a>
            <span className="text-gray-400">&gt;</span>
            <span className="text-gray-700 font-medium">Schemes</span>
          </nav>

          {/* Page Title & Share Button */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1 text-center">
              <h1 className="text-3xl sm:text-4xl font-extrabold text-[#111827] tracking-tight inline-block relative pb-2">
                <span className="border-b-[3px] border-govRed pb-1">Govern</span>ment Schemes
              </h1>
            </div>
            <button
              className="p-2 text-gray-500 hover:text-govNavy hover:bg-white rounded-full transition-colors border border-transparent hover:border-gray-200 shadow-xs"
              title="Share Page"
              onClick={() => {
                if (navigator.share) {
                  navigator.share({ title: 'Government Schemes | National Portal of India', url: window.location.href });
                }
              }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>

          {/* Schemes Descriptive Paragraph */}
          <p className="text-center text-sm sm:text-[15px] leading-relaxed text-gray-600 max-w-4xl mx-auto mb-8 font-normal">
            This section provides detailed information on various government schemes designed to benefit Indian citizens. Discover a range of programmes aimed at enhancing social welfare, economic development, health, education, and more. Access essential details about eligibility, application processes, and the specific advantages offered by each scheme, empowering you to take full advantage of the resources available to improve your quality of life.
          </p>

          {/* BEGIN: InteractiveSchemeFinderCard */}
          <section aria-labelledby="wizard-heading" className="bg-[#0c2340] text-white rounded-2xl shadow-xl overflow-hidden p-6 sm:p-10 border border-[#163155]" data-purpose="interactive-scheme-finder">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              {/* Left Column: Icon, Header, Steps Indicator */}
              <div className="lg:col-span-5 flex flex-col items-center text-center lg:border-r lg:border-blue-900/60 lg:pr-8">
                {/* Icon Representation */}
                <div className="w-20 h-20 mb-4 rounded-full border border-blue-400/30 flex items-center justify-center bg-blue-950/40 text-blue-300">
                  <svg className="w-12 h-12 stroke-current" fill="none" strokeWidth="1.5" viewBox="0 0 24 24">
                    <circle cx="12" cy="7" r="4" />
                    <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
                    <circle cx="4" cy="4" r="1.5" />
                    <circle cx="20" cy="4" r="1.5" />
                    <circle cx="20" cy="18" r="1.5" />
                    <circle cx="4" cy="18" r="1.5" />
                    <path d="M4 5.5v11M20 5.5v11M5.5 4h13M5.5 20h13" strokeDasharray="2 2" />
                  </svg>
                </div>
                <h2 className="text-2xl sm:text-[26px] font-bold leading-tight mb-2 tracking-tight" id="wizard-heading">
                  Find The Best Schemes For You In 6 Steps
                </h2>
                <p className="text-xs sm:text-sm text-gray-300 font-medium mb-4">
                  <span className="font-bold text-white">{wizardStep}</span> of 6 steps completed
                </p>
                {/* Stepper Progress Dots */}
                <div aria-label="Step progress" className="flex items-center justify-center space-x-1 sm:space-x-2 mb-6">
                  {[1, 2, 3, 4, 5, 6].map((s) => (
                    <React.Fragment key={s}>
                      <div
                        className={`w-7 h-7 rounded-full text-xs font-bold flex items-center justify-center transition-all ${
                          s === wizardStep
                            ? 'bg-white text-[#0c2340] shadow-md scale-110'
                            : s < wizardStep
                            ? 'bg-emerald-500 text-white'
                            : 'border border-gray-400 text-gray-300'
                        }`}
                      >
                        {s < wizardStep ? '✓' : s}
                      </div>
                      {s < 6 && <span className="text-gray-400 text-xs">...</span>}
                    </React.Fragment>
                  ))}
                </div>
                {/* Powered By Badge */}
                <div className="flex items-center space-x-2 text-xs text-gray-400">
                  <span>Powered by :</span>
                  <div className="bg-white text-[#0c2340] px-2 py-0.5 rounded-full font-bold text-xs tracking-tight flex items-center gap-1 shadow-xs">
                    <span className="text-govRed">my</span>
                    <span>Scheme</span>
                  </div>
                </div>
              </div>

              {/* Right Column: Form Question Elements */}
              <div className="lg:col-span-7 flex flex-col justify-center space-y-6 lg:pl-4">
                <div className="space-y-1">
                  <p className="text-xs text-gray-300">
                    Required fields are marked with an asterisk (<span className="text-red-400">*</span>)
                  </p>
                  <label className="block text-base sm:text-lg font-semibold text-white">
                    Tell us about yourself, you are a...
                  </label>
                </div>
                {/* Gender Selection Buttons */}
                <div aria-label="Select Gender" className="grid grid-cols-3 gap-3" role="radiogroup">
                  <button
                    className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg border transition-all text-sm font-medium focus:ring-2 focus:ring-white ${
                      selectedGender === 'male'
                        ? 'bg-blue-600 border-white text-white shadow-md'
                        : 'border-gray-500 hover:border-white bg-[#0e2c52] hover:bg-[#163a6b]'
                    }`}
                    type="button"
                    onClick={() => setSelectedGender('male')}
                  >
                    <span>♂</span> Male
                  </button>
                  <button
                    className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg border transition-all text-sm font-medium focus:ring-2 focus:ring-white ${
                      selectedGender === 'female'
                        ? 'bg-blue-600 border-white text-white shadow-md'
                        : 'border-gray-500 hover:border-white bg-[#0e2c52] hover:bg-[#163a6b]'
                    }`}
                    type="button"
                    onClick={() => setSelectedGender('female')}
                  >
                    <span>♀</span> Female
                  </button>
                  <button
                    className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg border transition-all text-sm font-medium focus:ring-2 focus:ring-white ${
                      selectedGender === 'transgender'
                        ? 'bg-blue-600 border-white text-white shadow-md'
                        : 'border-gray-500 hover:border-white bg-[#0e2c52] hover:bg-[#163a6b]'
                    }`}
                    type="button"
                    onClick={() => setSelectedGender('transgender')}
                  >
                    <span>⚧</span> Transgender
                  </button>
                </div>

                {/* Age Selection Dropdown */}
                <div className="flex flex-col sm:flex-row sm:items-center gap-3 pt-2">
                  <label className="text-base font-semibold text-white shrink-0" htmlFor="age-select">
                    <span className="text-red-400">*</span>And your age is
                  </label>
                  <div className="flex items-center gap-2">
                    <div className="relative w-44">
                      <select
                        className="w-full bg-[#0a1b32] text-white border border-gray-500 rounded-md py-2 px-3 text-sm focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none cursor-pointer"
                        id="age-select"
                        value={selectedAge}
                        onChange={(e) => setSelectedAge(e.target.value)}
                      >
                        <option value="">Select Age--</option>
                        <option value="18">18 Years</option>
                        <option value="25">25 Years</option>
                        <option value="30">30 Years</option>
                        <option value="35">35 Years</option>
                        <option value="45">45 Years</option>
                        <option value="60">60+ Years</option>
                      </select>
                    </div>
                    <span className="text-sm font-medium text-gray-200">Years</span>
                  </div>
                </div>

                {/* Action Controls: Next Button, Voice Filter, and Reset */}
                <div className="pt-4 flex flex-wrap items-center gap-4">
                  <button
                    className="w-36 py-2.5 bg-white text-[#0c2340] font-bold text-sm rounded-md shadow hover:bg-gray-100 transition-colors cursor-pointer text-center"
                    type="button"
                    onClick={handleNextWizardStep}
                  >
                    Next Step
                  </button>
                  <button
                    type="button"
                    onClick={() => onOpenAssistant(`I am a ${selectedAge || '25'} year old ${selectedGender || 'citizen'}. Check which schemes I can apply for.`)}
                    className="py-2.5 px-4 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-md shadow transition-colors inline-flex items-center gap-2 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[18px]">mic</span>
                    Speak With Sahaay
                  </button>
                  <button
                    className="inline-flex items-center text-xs text-gray-300 hover:text-white transition-colors cursor-pointer pt-1"
                    type="button"
                    onClick={handleResetForm}
                  >
                    <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    Reset Form
                  </button>
                </div>
              </div>
            </div>
          </section>
          {/* END: InteractiveSchemeFinderCard */}

          {/* BEGIN: SchemesByCategory */}
          <section aria-labelledby="category-heading" className="mt-16">
            <div className="text-center mb-8">
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight" id="category-heading">
                Schemes By Category
              </h2>
              <div className="h-1 w-16 bg-govRed mx-auto mt-2 rounded"></div>
            </div>
            {/* Category Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Card 1: Agriculture */}
              <div
                className={`bg-white p-5 rounded-xl border transition-all cursor-pointer flex flex-col items-center text-center group ${
                  selectedCategory === 'agriculture' ? 'ring-2 ring-govRed border-govRed shadow-md' : 'border-gray-200 hover:shadow-md'
                }`}
                onClick={() => handleCategoryCardClick('agriculture')}
              >
                <div className="w-12 h-12 bg-green-50 text-green-700 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h3 className="font-bold text-gray-800 text-sm mb-1 group-hover:text-blue-700">Agriculture & Rural</h3>
                <span className="text-xs text-gray-500">142 Schemes</span>
              </div>
              {/* Card 2: Healthcare */}
              <div
                className={`bg-white p-5 rounded-xl border transition-all cursor-pointer flex flex-col items-center text-center group ${
                  selectedCategory === 'healthcare' ? 'ring-2 ring-govRed border-govRed shadow-md' : 'border-gray-200 hover:shadow-md'
                }`}
                onClick={() => handleCategoryCardClick('healthcare')}
              >
                <div className="w-12 h-12 bg-red-50 text-red-600 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h3 className="font-bold text-gray-800 text-sm mb-1 group-hover:text-blue-700">Health & Wellness</h3>
                <span className="text-xs text-gray-500">89 Schemes</span>
              </div>
              {/* Card 3: Education & Learning */}
              <div
                className={`bg-white p-5 rounded-xl border transition-all cursor-pointer flex flex-col items-center text-center group ${
                  selectedCategory === 'education' ? 'ring-2 ring-govRed border-govRed shadow-md' : 'border-gray-200 hover:shadow-md'
                }`}
                onClick={() => handleCategoryCardClick('education')}
              >
                <div className="w-12 h-12 bg-blue-50 text-blue-700 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M12 14l9-5-9-5-9 5 9 5z" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h3 className="font-bold text-gray-800 text-sm mb-1 group-hover:text-blue-700">Education & Skills</h3>
                <span className="text-xs text-gray-500">114 Schemes</span>
              </div>
              {/* Card 4: Business & Finance */}
              <div
                className={`bg-white p-5 rounded-xl border transition-all cursor-pointer flex flex-col items-center text-center group ${
                  selectedCategory === 'social_welfare' ? 'ring-2 ring-govRed border-govRed shadow-md' : 'border-gray-200 hover:shadow-md'
                }`}
                onClick={() => handleCategoryCardClick('social_welfare')}
              >
                <div className="w-12 h-12 bg-amber-50 text-amber-700 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h3 className="font-bold text-gray-800 text-sm mb-1 group-hover:text-blue-700">Business & MSME</h3>
                <span className="text-xs text-gray-500">95 Schemes</span>
              </div>
            </div>
          </section>
          {/* END: SchemesByCategory */}

          {/* BEGIN: Live Schemes Directory & Filter Section */}
          <section id="schemes-catalogue-section" className="mt-16">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Verified Government Schemes</h2>
                <p className="text-xs text-gray-500">Official welfare programs with real deterministic rule checking and instant application support</p>
              </div>
              {selectedCategory && (
                <button
                  type="button"
                  onClick={() => setSelectedCategory(null)}
                  className="text-xs text-govRed font-bold hover:underline"
                >
                  Clear Category Filter ({selectedCategory})
                </button>
              )}
            </div>

            <SchemeListings
              schemes={schemes}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              selectedCategory={selectedCategory}
              onSelectCategory={setSelectedCategory}
              onViewDetails={(scheme) => setActiveModalScheme(scheme)}
              onAskAssistant={handleAskAssistantAboutScheme}
              loading={loading}
              error={error}
            />
          </section>
          {/* END: Live Schemes Directory */}
        </div>
      </main>
      {/* END: MainContent */}

      {/* BEGIN: FloatingUtilityDock (Right edge icons seen in screenshot) */}
      <aside className="fixed right-0 top-1/2 -translate-y-1/2 flex flex-col space-y-1 z-30 shadow-md">
        <button className="w-10 h-10 bg-gray-500 hover:bg-[#0c2340] text-white flex items-center justify-center rounded-l-md transition-colors" title="Feedback">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <button className="w-10 h-10 bg-gray-500 hover:bg-[#0c2340] text-white flex items-center justify-center rounded-l-md transition-colors" title="Screen Reader Support">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <button className="w-10 h-10 bg-gray-500 hover:bg-[#0c2340] text-white flex items-center justify-center rounded-l-md transition-colors" title="Government Calendar">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <button className="w-10 h-10 bg-gray-500 hover:bg-[#0c2340] text-white flex items-center justify-center rounded-l-md transition-colors" title="Share Portal">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <button className="w-10 h-10 bg-gray-500 hover:bg-[#0c2340] text-white flex items-center justify-center rounded-l-md transition-colors" title="Accessibility Center">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </aside>
      {/* END: FloatingUtilityDock */}

      {/* BEGIN: SahaayVoiceAssistantWidget Launcher */}
      <div className="fixed bottom-36 right-6 z-50 flex flex-col items-end gap-2.5 select-none" data-purpose="sahaay-assistant">
        {/* Eye-catching status pill tag */}
        <div
          onClick={() => onOpenAssistant()}
          className="flex items-center gap-2 bg-[#0c2340] text-white text-xs font-bold px-3.5 py-1.5 rounded-full shadow-xl border border-blue-400/30 backdrop-blur-xs transition-transform hover:scale-105 cursor-pointer"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span>Sahaay Voice Assistant • Tap or Speak</span>
        </div>
        {/* Large glowing assistant launcher with multi-layer pulse rings */}
        <div className="relative flex items-center justify-center">
          {/* Outer pulse aura rings */}
          <span className="animate-ping absolute inline-flex h-20 w-20 rounded-full bg-orange-600/30"></span>
          <span className="absolute inline-flex h-[76px] w-[76px] rounded-full bg-gradient-to-tr from-orange-600 via-govRed to-pink-600 opacity-30 blur-sm"></span>
          {/* Main interactive button */}
          <button
            aria-label="Sahaay Voice Assistant - Tap or speak to search"
            className="relative w-16 h-16 rounded-full bg-gradient-to-r from-orange-600 via-govRed to-pink-600 text-white flex items-center justify-center shadow-2xl hover:scale-110 active:scale-95 transition-all duration-200 border-2 border-white focus:outline-none cursor-pointer group"
            id="sahaay-launcher"
            title="Sahaay Voice Assistant - Tap or speak to search"
            type="button"
            onClick={() => onOpenAssistant()}
          >
            {/* High-fidelity Microphone & Frequency Wave Icon */}
            <svg className="w-8 h-8 text-white transition-transform group-hover:scale-110" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
              <rect fill="white" fillOpacity="0.15" height="11" rx="3" stroke="currentColor" strokeWidth="1.8" width="6" x="9" y="2" />
              <path d="M5 10a7 7 0 0 0 14 0" strokeLinecap="round" strokeLinejoin="round" />
              <line strokeLinecap="round" x1="12" x2="12" y1="17" y2="21" />
              <line strokeLinecap="round" x1="8" x2="16" y1="21" y2="21" />
              <path d="M2 9v2M22 9v2M19 6.5a10 10 0 0 1 0 7M5 6.5a10 10 0 0 0 0 7" opacity="0.9" strokeLinecap="round" strokeWidth="1.5" />
            </svg>
            {/* Active live dot indicator */}
            <span className="absolute top-1 right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-white border border-govRed"></span>
            </span>
          </button>
        </div>
      </div>
      {/* END: SahaayVoiceAssistantWidget Launcher */}

      {/* BEGIN: Footer */}
      <footer className="bg-gray-900 text-gray-400 text-xs py-6 border-t border-gray-800" data-purpose="site-footer">
        <div className="max-w-[1536px] mx-auto px-4 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p>© Content Owned, Updated and Maintained by National Informatics Centre (NIC), Ministry of Electronics & IT, Government of India.</p>
          <div className="flex items-center space-x-4">
            <a className="hover:text-white transition-colors" href="#">Privacy Policy</a>
            <span>|</span>
            <a className="hover:text-white transition-colors" href="#">Terms of Use</a>
            <span>|</span>
            <a className="hover:text-white transition-colors" href="#">Help</a>
          </div>
        </div>
      </footer>
      {/* END: Footer */}

      {/* Scheme Detail Modal */}
      {activeModalScheme && (
        <SchemeDetailModal
          scheme={activeModalScheme}
          onClose={() => setActiveModalScheme(null)}
          onAskAssistant={handleAskAssistantAboutScheme}
        />
      )}
    </div>
  );
};
