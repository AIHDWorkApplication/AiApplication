import React from 'react';
import { useState } from 'react';

function VideoStream() {
  const [isRunning, setIsRunning] = useState(false);

  const handleToggle = async () => {
    try {
      const response = await fetch('http://localhost:5000/toggle_webcam', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setIsRunning(data.is_running); // Ensure the state is updated correctly
      }
    } catch (error) {
      console.error('Error toggling webcam:', error);
    }
  };
  

  return (
    <div>
      <header className="feature-box top">
        <nav>
          <li><a href="/home">back to home</a></li>
        </nav>
      </header>
      <video
  autoPlay
  controls
  src="http://localhost:5000/webapp"
  type="video/mp4"
  style={{ width: '900px', height: '600px', borderRadius: '35px' }}
/>
      <button onClick={handleToggle}>
        {isRunning ? 'Stop Webcam' : 'Start Webcam'}
      </button>
    </div>
  )
}

export default VideoStream;
