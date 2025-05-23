'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import WebcamCapture from '@/components/WebcamCapture';
import Webcam from 'react-webcam';

declare global {
  interface Window {
    webkitSpeechRecognition: any;
    SpeechRecognition: any;
  }
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
}

interface IntentResponse {
  intent: string;
  description?: string;
}

export default function Home() {
  const [chatMessages, setChatMessages] = useState<Array<{ type: 'user' | 'ai'; text: string }>>([]);
  const webcamRef = useRef<Webcam>(null);
  const [intentMessage, setIntentMessage] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);
  const shouldListenRef = useRef<boolean>(true);

  // Cleanup function for speech synthesis and recognition
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      window.speechSynthesis.cancel();
    };
  }, []);

  const handleBufferCapture = async (frames: string[]) => {
    if (!frames.length) return;
    
    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/analyze-buffer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frames }),
      });

      if (!response.ok) throw new Error('Failed to analyze gesture sequence');

      const data: IntentResponse = await response.json();
      setIntentMessage(data.intent);
      
      // Automatically speak the interpreted intent
      speak(data.intent);
      setChatMessages(prev => [...prev, { type: 'ai', text: data.intent }]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze gesture sequence';
      setError(errorMessage);
      setChatMessages(prev => [...prev, { type: 'ai', text: `Error: ${errorMessage}` }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const speak = useCallback((text: string) => {
    if (!text || speaking) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    setSpeaking(true);
    const utterance = new SpeechSynthesisUtterance(text);
    
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => {
      setSpeaking(false);
      setError('Failed to speak the message');
    };
    
    window.speechSynthesis.speak(utterance);
  }, [speaking]);

  const handleCommand = useCallback(async (command: string) => {
    if (!command.trim()) return;
    
    const commandLower = command.toLowerCase();
    setChatMessages(prev => [...prev, { type: 'user', text: command }]);

    try {
      if (commandLower.includes('stop listening')) {
        shouldListenRef.current = false;
        recognitionRef.current?.stop();
        setIsListening(false);
        const response = "Okay, I'll stop listening. Click the Talk to AI button when you want to chat again.";
        speak(response);
        setChatMessages(prev => [...prev, { type: 'ai', text: response }]);
      } else if (commandLower.includes('describe')) {
        const frame = webcamRef.current?.getScreenshot();
        if (frame) {
          const initialResponse = "Analyzing the image...";
          speak(initialResponse);
          setChatMessages(prev => [...prev, { type: 'ai', text: initialResponse }]);

          try {
            const response = await fetch('http://localhost:8000/api/describe-image', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ image: frame }),
            });

            if (!response.ok) throw new Error('Failed to describe image');

            const data = await response.json();
            if (data.description) {
              speak(data.description);
              setChatMessages(prev => [...prev, { type: 'ai', text: data.description }]);
            } else {
              throw new Error('No description received');
            }
          } catch (error) {
            const errorMessage = "I'm sorry, I couldn't describe the image at the moment.";
            speak(errorMessage);
            setChatMessages(prev => [...prev, { type: 'ai', text: errorMessage }]);
          }
        }
      } else if (commandLower.includes('hello') || commandLower.includes('hi')) {
        const response = "Hello! I can help you with gestures, or I can describe what I see. Just ask me to 'describe' or make a gesture.";
        speak(response);
        setChatMessages(prev => [...prev, { type: 'ai', text: response }]);
      } else if (commandLower.includes('how are you')) {
        const response = "I'm doing well! I can help you with gestures or describe what I see. What would you like me to do?";
        speak(response);
        setChatMessages(prev => [...prev, { type: 'ai', text: response }]);
      } else {
        const response = "I heard you say: " + command + ". You can ask me to 'describe' what I see, or say 'stop listening' to end our conversation.";
        speak(response);
        setChatMessages(prev => [...prev, { type: 'ai', text: response }]);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      setChatMessages(prev => [...prev, { type: 'ai', text: `Error: ${errorMessage}` }]);
    }
  }, [speak]);

  const startListening = useCallback(() => {
    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        throw new Error('Speech recognition is not supported in your browser.');
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false;
      shouldListenRef.current = true;

      recognition.onstart = () => {
        setIsListening(true);
        const welcomeMessage = "I'm listening... You can say 'describe' to get an image description, or 'stop listening' to end the conversation.";
        setChatMessages(prev => [...prev, { type: 'ai', text: welcomeMessage }]);
        speak(welcomeMessage);
      };

      recognition.onend = () => {
        if (shouldListenRef.current) {
          try {
            recognition.start();
          } catch (error) {
            setIsListening(false);
          }
        } else {
          setIsListening(false);
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        const errorMessage = 'Sorry, there was an error with speech recognition.';
        speak(errorMessage);
        setChatMessages(prev => [...prev, { type: 'ai', text: errorMessage }]);
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const results = event.results;
        const lastResult = results[results.length - 1];
        if (lastResult && lastResult[0]) {
          const transcript = lastResult[0].transcript.trim();
          if (transcript) {
            handleCommand(transcript);
          }
        }
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start voice recognition';
      setError(errorMessage);
      setChatMessages(prev => [...prev, { type: 'ai', text: `Error: ${errorMessage}` }]);
    }
  }, [handleCommand]);

  return (
    <div className="min-h-screen p-4 md:p-8 bg-gray-100">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <h1 className="text-3xl font-bold text-center mb-8">
              Gesture Recognition
            </h1>
            <WebcamCapture onBufferCapture={handleBufferCapture} webcamRef={webcamRef} />
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col gap-4">
            {isProcessing && (
              <div className="flex items-center justify-center p-6 bg-white rounded-lg shadow-md">
                <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-3" />
                Analyzing gesture sequence...
              </div>
            )}

            {intentMessage && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">Interpreted Intent</h3>
                    <p className="text-gray-700">{intentMessage}</p>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => speak(intentMessage)}
                    disabled={speaking}
                    className={`px-4 py-2 ${speaking ? 'bg-gray-400' : 'bg-purple-600 hover:bg-purple-700'} text-white rounded-lg shadow-md transition-colors`}
                  >
                    {speaking ? 'Speaking...' : '🔊 Speak'}
                  </motion.button>
                </div>
              </motion.div>
            )}

            {error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {error}
              </motion.div>
            )}

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={startListening}
                disabled={isListening}
                className={`w-full px-6 py-3 ${isListening ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'} text-white rounded-lg shadow-md transition-colors flex items-center justify-center gap-2`}
              >
                {isListening ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Listening...
                  </>
                ) : (
                  <>🎙️ Talk to AI</>
                )}
              </motion.button>

              <div className="bg-white rounded-lg shadow-md p-4 max-h-96 overflow-y-auto">
                <div className="space-y-4">
                  {chatMessages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.type === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-black'
                        }`}
                      >
                        <p>{message.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}