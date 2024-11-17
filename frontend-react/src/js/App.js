import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link} from 'react-router-dom';
import { useEffect, useState } from 'react';
import Home from './Home';
import Video from './VideoStream';

function App() {
  return (
    <Router>
      <div>
      <Home />
        <Routes>
          <Route path="/video" element={<Video />} />
          <Route path="/webcam" element={<Video />} />
          {/* Add other routes as needed */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
