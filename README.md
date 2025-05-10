# Neuro-Bridge

Neuro-Bridge is a real-time gesture recognition application that interprets facial gestures and movements into meaningful communication intents. It uses computer vision and AI to help bridge communication gaps for people with limited verbal abilities.

## Features

- Real-time facial gesture recognition
- Movement pattern analysis (head nods, shakes, blinks)
- Intent interpretation using AI
- Text-to-speech output for interpreted intents
- Responsive web interface with real-time feedback

## Tech Stack

### Frontend
- Next.js 15.3
- React 19
- TypeScript
- Tailwind CSS
- Framer Motion for animations
- React Webcam for camera integration

### Backend
- FastAPI
- MediaPipe for facial landmark detection
- OpenRouter API for intent interpretation
- Python 3.x
- OpenCV for image processing

## Getting Started

### Prerequisites
- Node.js (Latest LTS version recommended)
- Python 3.x
- pip (Python package manager)

### Installation

## 1. Clone the repository:
git clone https://github.com/yourusername/neuro-bridge.git
cd neuro-bridge

## 2. Set up the frontend:
cd frontend
npm install

## 3. Set up the backend:
cd backend
pip install -r requirements.txt

## 4. Environment Configuration:
   - Create a .env file in the backend directory
   - Add your OpenRouter API key:
     OPENROUTER_API_KEY=your_api_key_here

### Running the Application
1. Start the backend server:
cd backend
uvicorn main:app --reload


## 2. Start the frontend development server:
cd frontend
npm run dev

## 3. Open your browser and navigate to http://localhost:3000
## Usage
1. Allow camera access when prompted
2. Click the "Record Intent" button to start gesture recording
3. Make a gesture (nod, shake head, blink, etc.)
4. The application will interpret your gesture and display the interpreted intent
5. Use the speak button to hear the interpretation through text-to-speech