import React from 'react';
import { VoiceState } from '../types';

interface WaveformVisualizerProps {
  state: VoiceState;
  audioLevel?: number; // 0 to 1
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({ state, audioLevel = 0 }) => {
  const isListening = state === 'listening';
  const isSpeaking = state === 'speaking';
  const isProcessing = state === 'processing';

  // Number of visualizer bars
  const bars = [0.25, 0.5, 0.85, 0.65, 1.0, 0.75, 0.45, 0.9, 0.55, 0.35, 0.7, 0.4];

  return (
    <div className="flex items-center justify-center gap-1.5 h-12 px-4 py-2">
      {bars.map((baseHeight, i) => {
        let heightMultiplier = 0.2;
        if (isListening) {
          const dynamicBoost = Math.max(0.2, audioLevel * 1.6);
          heightMultiplier = Math.min(1.0, baseHeight * dynamicBoost * (0.8 + 0.4 * Math.sin(Date.now() / 200 + i)));
        } else if (isSpeaking) {
          heightMultiplier = 0.3 + 0.7 * Math.abs(Math.sin((Date.now() / 150) + i * 0.7));
        } else if (isProcessing) {
          heightMultiplier = 0.2 + 0.4 * Math.abs(Math.sin((Date.now() / 300) + i * 0.5));
        }

        const heightPercent = Math.max(12, Math.round(heightMultiplier * 100));

        return (
          <div
            key={i}
            className={`w-1.5 rounded-full transition-all duration-150 ${
              isListening
                ? 'bg-red-500 shadow-sm shadow-red-300'
                : isSpeaking
                ? 'bg-blue-600 shadow-sm shadow-blue-300'
                : isProcessing
                ? 'bg-amber-500 animate-pulse'
                : 'bg-gray-300'
            }`}
            style={{
              height: `${heightPercent}%`,
              minHeight: '4px',
            }}
          />
        );
      })}
    </div>
  );
};
