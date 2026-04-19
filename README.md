🚦 Smart Traffic Control Simulation

Intelligent traffic signal system using adaptive control, emergency prioritization, and real-time analytics.

📌 Overview

The Smart Traffic Control Simulation is a Python-based project that models a realistic 4-way urban intersection.

It compares traditional fixed-timer signals with an adaptive signal system that responds to traffic conditions in real time.

The system also handles emergency vehicles and simulates real-world conditions like rain and night.

🎯 Why This Project Matters
Static traffic lights are inefficient in real-world conditions
Emergency vehicles face delays in normal traffic
Weather and visibility impact road safety
Data-driven traffic solutions need simulation-based testing
✨ Key Features
🚥 Smart Traffic Control
Fixed timing signal system
Adaptive signal control based on:
Traffic density
Average waiting time
Pedestrian crossing support
Emergency signal override
🚑 Emergency Handling
Detects emergency vehicles
Gives priority green signal
Forces other vehicles to yield
🚗 Vehicle Simulation
Acceleration and deceleration
Safe following distance
Reaction delay near intersections
Lane changing when safe
🌧️ Environmental Conditions
Rain mode → reduced speed, increased spacing
Night mode → reduced visibility, slower reaction
Combined effects for realism
📊 Analytics & Output
Tracks:
Waiting time
Throughput
Congestion
CSV export
Graphs using matplotlib
🎮 Controls
Key	Action
P	Pedestrian Crossing
Space	Pause / Resume
R	Toggle Rain
N	Toggle Night
E	Spawn Emergency Vehicle
D	Debug Mode
🛠️ Tech Stack
Python 3
Pygame
Matplotlib
CSV module
▶️ Run the Project
pip install pygame matplotlib
python main.py
📷 Demo

Add screenshots here after running the simulation:

assets/screenshot1.png
assets/screenshot2.png
🚀 Key Highlights
Real-time interactive simulation
Adaptive decision-making system
Emergency-aware traffic control
Environment-based behavior modeling
Data-driven performance evaluation
🔮 Future Improvements
AI/ML-based signal optimization
Multi-intersection traffic system
Real-world data integration
👤 Author

Melba Varghese
https://github.com/melbavarghesecbe-svg

⭐ Final Note

This project demonstrates how simulation and intelligent control can be used to solve real-world traffic problems.
