'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import WebcamCapture from '@/components/WebcamCapture';

interface IntentResponse {
  intent: string;
}

export default function Home() {
  const [intentMessage, setIntentMessage] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBufferCapture = async (frames: string[]) => {
    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/analyze-buffer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ frames }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze gesture sequence');
      }

      const data: IntentResponse = await response.json();
      setIntentMessage(data.intent);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze gesture sequence');
    } finally {
      setIsProcessing(false);
    }
  };

  const speak = (text: string) => {
    if (!text || speaking) return;
    
    setSpeaking(true);
    const utterance = new SpeechSynthesisUtterance(text);
    
    utterance.onend = () => {
      setSpeaking(false);
    };
    
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="min-h-screen p-4 md:p-8 bg-gray-1000">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <h1 className="text-3xl font-bold text-center mb-8">
              Gesture Recognition
            </h1>
            <WebcamCapture onBufferCapture={handleBufferCapture} />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex flex-col gap-4 text-black"
          >
            {isProcessing && (
              <div className="flex items-center justify-center p-6 bg-white rounded-lg shadow-md">
                <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-3" />
                Analyzing gesture sequence...
              </div>
            )}

            {intentMessage && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-lg shadow-md p-6"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">Interpreted Intent</h3>
                    <p className="text-gray-700">{intentMessage}</p>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => speak(intentMessage)}
                    disabled={speaking || !intentMessage}
                    className={`px-4 py-2 ${
                      speaking ? 'bg-gray-400' : 'bg-purple-600 hover:bg-purple-700'
                    } text-white rounded-lg shadow-md transition-colors`}
                  >
                    {speaking ? 'Speaking...' : '🔊 Speak'}
                  </motion.button>
                </div>
              </motion.div>
            )}

            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg"
              >
                {error}
              </motion.div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
