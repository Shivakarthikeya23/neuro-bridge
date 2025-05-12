'use client';

import React, { useCallback, useRef, useState } from 'react';
import Webcam from 'react-webcam';
import { motion } from 'framer-motion';
import { RefObject } from 'react';

interface WebcamCaptureProps {
  onBufferCapture: (frames: string[]) => void;
  webcamRef: RefObject<Webcam | null>;
}

const WebcamCapture: React.FC<WebcamCaptureProps> = ({ onBufferCapture, webcamRef }) => {
  const [isRecording, setIsRecording] = useState(false);
  const frameBufferRef = useRef<string[]>([]);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = useCallback(() => {
    if (isRecording) return;
    
    setIsRecording(true);
    frameBufferRef.current = [];
    let frameCount = 0;
    
    // Increased frame rate for better gesture detection
    recordingIntervalRef.current = setInterval(() => {
      const frame = webcamRef.current?.getScreenshot();
      if (frame) {
        frameBufferRef.current.push(frame);
        frameCount++;
        
        // Capture 10 frames in 1 second for faster response
        if (frameCount >= 10) {
          if (recordingIntervalRef.current) {
            clearInterval(recordingIntervalRef.current);
          }
          setIsRecording(false);
          onBufferCapture(frameBufferRef.current);
        }
      }
    }, 100); // 10 FPS for smoother capture
    
    // Safety timeout to ensure recording stops
    setTimeout(() => {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
        setIsRecording(false);
        if (frameBufferRef.current.length > 0) {
          onBufferCapture(frameBufferRef.current);
        }
      }
    }, 2000);
  }, [isRecording, onBufferCapture, webcamRef]);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center gap-4"
    >
      <Webcam
        ref={webcamRef}
        audio={false}
        screenshotFormat="image/jpeg"
        className="rounded-lg shadow-lg w-full max-w-2xl"
        videoConstraints={{
          width: 640,
          height: 480,
          facingMode: "user",
          frameRate: 30
        }}
      />
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={startRecording}
        disabled={isRecording}
        className={`px-6 py-3 ${
          isRecording ? 'bg-gray-400' : 'bg-green-600 hover:bg-green-700'
        } text-white rounded-lg shadow-md transition-colors flex items-center gap-2`}
      >
        {isRecording ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Recording...
          </>
        ) : (
          <>
            🎥 Record Intent
          </>
        )}
      </motion.button>
    </motion.div>
  );
};

export default WebcamCapture;