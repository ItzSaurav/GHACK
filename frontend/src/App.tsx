import React, { useState, useEffect } from 'react';
import { HostPortal } from './portal/HostPortal';
import { SchemeAssistantWidget } from './assistant/SchemeAssistantWidget';

export const App: React.FC = () => {
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  const [externalPrompt, setExternalPrompt] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleOpenAssistant = (prompt?: string) => {
    setIsAssistantOpen(true);
    if (prompt) {
      setExternalPrompt(prompt);
    }
  };

  return (
    <div className="sahaay-application-root">
      {/* Offline Alert Strip */}
      {!isOnline && (
        <div className="offline-warning-strip" role="alert">
          <span>You are currently in offline mode. Local scheme directory is available. Reconnect for voice assistance.</span>
        </div>
      )}

      {/* Host Portal: Realistic Static Government Schemes Discovery Portal */}
      <HostPortal onOpenAssistant={handleOpenAssistant} />

      {/* Embedded Assistant Widget: Reusable Floating Multi-lingual Voice Assistant */}
      <SchemeAssistantWidget
        isOpen={isAssistantOpen}
        onToggle={() => setIsAssistantOpen(!isAssistantOpen)}
        externalPrompt={externalPrompt}
        onClearExternalPrompt={() => setExternalPrompt(null)}
      />
    </div>
  );
};

export default App;
