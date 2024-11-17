import React from 'react';
import '../css/Home.css'; // Create a separate CSS file to include your styles

function HeaderComponent() {
  return (
    <header className="feature-box right">
      <nav>
        <ul>
          <li><a href="/home">Home</a></li>
          <li><a href="/video">Video</a></li>
          <li><a href="/webcam">LiveWebcam</a></li>
        </ul>
      </nav>
    </header>
  );
}

export default HeaderComponent;
