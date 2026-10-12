Please share the proposed Title for Your Project Idea? *

A Vision-Free Autonomous Vacuum with Edge AI Predictive Maintenance


What problem is being solved by your proposed project? *


Standard consumer robot vacuums suffer from three major flaws: they are privacy hazards due to cloud-connected onboard cameras, they lack intuitive user feedback (relying on cryptic error codes), and they fail catastrophically without warning due to mechanical wear.
Furthermore, commercial vacuums are prohibitively expensive and often function as unrepairable, disposable appliances when mechanical parts wear out. This project solves these issues by building a fully open-source, local-first robot vacuum that is highly cost-effective and designed for longevity. It navigates precisely using affordable non-optical sensors (LiDAR and ToF) and utilizes TinyML for predictive mechanical maintenance to prevent breakdowns


Please share details of your project idea: *

Most robot vacuums today suffer from three major issues: they are expensive, they rely on privacy-invading cameras to navigate, and they fail suddenly without warning. My project, A Vision-Free Autonomous Vacuum with Edge AI Predictive Maintenance, solves this by building a custom, affordable floorcare robot from scratch that prioritizes privacy, longevity, and human-robot interaction.


The project relies entirely on the dual-brain architecture of the Arduino Uno Q to keep costs down, It breaks down into three main features:


Privacy-First Navigation: Instead of mapping homes with cameras, the robot uses a completely vision-free sensor stack. A standard 2D LiDAR handles room mapping, while a "virtual bumper" made of Time-of-Flight (ToF) and ultrasonic sensors detects low-lying clutter (like cables) and transparent obstacles (like glass). The Linux side of the Uno Q handles the heavy ROS 2 navigation stack seamlessly.


Predictive Maintenance via Edge AI: To stop the vacuum from acting like a disposable appliance, the Uno Q's real-time microcontroller will monitor inline current sensors attached to the motors. A local TinyML model will learn the normal electrical "effort" required to clean. If a brush starts to tangle or a filter clogs, the AI detects the subtle shift in current and warns the user long before the motor burns out.


Standard vacuums just beep cryptic error codes. Drawing from my background in kinetic art, I am programming the vacuum to communicate through organic movement. If the predictive maintenance model detects a jammed brush, the robot will do a quick "frustrated shake" and shut down. If the ToF sensors spot a new obstacle, it will slow down and do a cautious "investigative" arc. It is a smarter, friendlier way for the hardware to tell the user what it needs.


Which of the following board(s) are you planning to use for your proposed project? *

Arduino Uno Q 


What role will this board play in your project? *

The Arduino Uno Q is going to act as both the main brain and the central nervous system for the entire vacuum. The main reason I picked this board is because of its dual architecture, which lets me completely drop the need for a secondary board like a Raspberry Pi. It keeps the hardware stack much cleaner and cheaper.
I'll be splitting the workload between the two sides of the board. The Qualcomm processor running Linux will handle all the heavy computational lifting, like running the ROS 2 navigation stack, processing the 2D LiDAR data, and managing the SLAM room mapping.
At the exact same time, the real-time STM32 microcontroller on the board will handle the robot's physical reflexes. It will continuously poll the Time-of-Flight and ultrasonic sensors, read the inline motor current data to run the TinyML predictive maintenance model, and push the actual drive commands to the motors. This real-time control is what will actually allow the vacuum to perform those fluid, kinetic personality movements without any lag.



Are there any aspects that make your project unique from similar projects online? *

Most open-source or DIY vacuum projects onlind USB-C Hub (To handle data/power distribution to the LiDAR without browning out the Uno Q).
Sensors (Navigation & Edge AI Maintenance)
- Primary Ranging & Obstacle Detection: GY-53 VL53L0X Laser Time-of-Flight (ToF) Distance Ranging Sensor (front obstacle scanning).
- Cliff/Drop & Corner Sensors: TCRT5000 IR Reflective Sensors (from lab inventory) pointing downward for stair prevention and corner collision detection.
- Main Mapping (Future Phase): 2D 360-degree LiDAR (e.g., YDLIDAR X3 or RPLIDAR A1).
- Tactile Fail-safes: Snap-Action Microswitches for physical bumper and wheel-drop detection.
- Predictive Maintenance: INA219 High-Side DC Current Sensor Breakouts to monitor motor loads.
- Odometry: Built-in wheel encoders / optical encoder discs on drive wheels.

Actuators & Motors
- Drive System: 2x 3V-6V TT DC Gear Motors (1:48 ratio) on a 2WD differential drive chassis with caster wheel.
- Suction: 5V DC Centrifugal Blower Fan (5015 blower) for dust collection.
- Sweeping: Small 5V DC motor for edge brush.

Power Supply & Motor Control
- Main Power: Single 5V power source (standard 5V USB power bank or single lithium battery pack, eliminating separate external power supplies).
- Voltage Regulation: Onboard 5V rail distribution with common ground reference.
- Motor Controllers: TB6612FNG or L298N Dual Motor Driver (5V logic compatible).
- Blower Control: Logic-level N-Channel MOSFET switch module (e.g., IRLZ44N or AO3400) for PWM speed control.



Describe the programming language(s), frameworks, IDEs, or platforms you plan to use. Briefly explain how you will develop, program, and test your design (e.g., Arduino IDE with C++, MicroPython on ESP32, STM32CubeIDE, etc.).*


I will develop the software using Visual Studio Code (Remote-SSH), leveraging AI assistants like Gemini and Claude to rapidly prototype and optimize code for the Arduino Uno Q's dual-processor architecture.
The real-time STM32 MCU will be programmed in C++ (Arduino Core/Zephyr OS) to handle deterministic tasks like motor PID control, sensor polling, and running a TinyML predictive maintenance model trained via Edge Impulse. Meanwhile, the Qualcomm MPU running Debian Linux will use ROS 2 (Python and C++) for SLAM mapping and path planning based on LiDAR data. The two processors will communicate via the Arduino Bridge Library (RPC), passing velocity commands and odometry.
I will test iteratively: first validating the MCU's motor control and Edge AI with standalone C++ sketches, then testing thmapping in Linux, and finally bridging both systems for live physical testing, using AI to quickly debug the integration.
Yes, I have published hardware and embedded systems projects online on both Autodesk Instructables and Hackster.io.
