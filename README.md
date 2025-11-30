# MediaPipe Hand Gesture Recognition for Home Assistant

🤚 A Home Assistant Addon that performs real-time hand gesture recognition using MediaPipe and integrates with Home Assistant via MQTT Auto Discovery.

> **Note**: This is a Home Assistant Addon. For installation instructions, see [INSTALL.md](INSTALL.md).

## Features

- **Real-time Hand Gesture Recognition**: Uses MediaPipe Hands to detect and classify gestures
- **MQTT Integration**: Seamless integration with Home Assistant using MQTT Auto Discovery
- **Robust Video Streaming**: Automatic RTSP reconnection with configurable retry logic
- **State Machine & Debouncing**: Prevents false triggers with stability checks and cooldown mechanisms
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Configurable**: All parameters can be adjusted via environment variables

## Recognized Gestures

1. **Open Palm**: All five fingers extended
2. **Closed Fist**: All fingers curled
3. **Pointing Up**: Only index finger extended
4. **OK Sign**: Thumb and index finger touching, other fingers extended
5. **None**: No hand detected or unclear gesture

## Requirements

- Docker and Docker Compose
- RTSP-compatible camera
- Home Assistant with Mosquitto MQTT broker
- Network access between all components

## Quick Start

### 1. Clone and Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Update Configuration

Edit `docker-compose.yml` or `.env` file with your settings:

```bash
RTSP_URL=rtsp://username:password@camera-ip:554/stream1
MQTT_BROKER=homeassistant-ip
MQTT_PORT=1883
MQTT_USERNAME=mqtt-user
MQTT_PASSWORD=mqtt-password
```

### 3. Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Check Home Assistant

After starting the service, a new sensor entity should appear in Home Assistant:

- Entity ID: `sensor.gesture_control`
- Entity Name: "Gesture Control"
- States: Open Palm, Closed Fist, Pointing Up, OK Sign, None

## Configuration Parameters

### Video Processing

- `FRAME_WIDTH`: Frame width for processing (default: 640)
- `FRAME_HEIGHT`: Frame height for processing (default: 480)
- `TARGET_FPS`: Target processing frame rate (default: 10)

### Gesture Recognition

- `GESTURE_CONFIDENCE_THRESHOLD`: Minimum confidence to accept detection (default: 0.8)
- `GESTURE_STABLE_DURATION`: How long gesture must be stable before triggering (default: 0.5 seconds)
- `GESTURE_COOLDOWN`: Cooldown period between repeated gestures (default: 2.0 seconds)

### Connection

- `RTSP_RECONNECT_DELAY`: Delay between RTSP reconnection attempts (default: 5 seconds)

## Architecture

```
main.py                          # Main application loop
├── VideoStreamProcessor         # RTSP stream handling with auto-reconnect
├── GestureEngine               # MediaPipe Hands wrapper
│   └── Gesture recognition     # Geometric landmark analysis
├── GestureBuffer               # State machine & debouncing logic
└── MQTTClient                  # MQTT connection & HA Discovery
```

## How It Works

### 1. Video Stream Processing

- Connects to RTSP stream with automatic reconnection
- Resizes frames for optimal performance
- Implements frame rate limiting to reduce CPU usage

### 2. Gesture Recognition

MediaPipe detects 21 hand landmarks. Gestures are recognized by analyzing:

- **Finger Extension**: Comparing tip position with PIP/MCP joints
- **Thumb State**: Distance from palm center
- **Geometric Relationships**: Distance between specific landmarks (e.g., thumb-index distance for OK sign)

### 3. State Machine & Debouncing

```
Detection → Buffer → Stability Check → Cooldown Check → Trigger → MQTT Publish
```

- Gestures must remain stable for `GESTURE_STABLE_DURATION` seconds
- Once triggered, same gesture won't re-trigger for `GESTURE_COOLDOWN` seconds
- Different gestures can trigger immediately

### 4. MQTT & Home Assistant

- On startup, sends MQTT Discovery configuration to Home Assistant
- Creates a sensor entity automatically
- Publishes gesture state as JSON: `{"gesture": "CLOSED_FIST", "confidence": 0.95, "timestamp": 1234567890}`

## Troubleshooting

### Container crashes or restarts

Check logs:
```bash
docker-compose logs -f
```

### RTSP connection fails

- Verify RTSP URL is correct
- Check network connectivity to camera
- Ensure camera supports RTSP

### MQTT not connecting

- Verify MQTT broker IP and port
- Check MQTT credentials
- Ensure Home Assistant's Mosquitto addon is running

### Gestures not detected

- Ensure good lighting conditions
- Keep hand within camera view
- Adjust `GESTURE_CONFIDENCE_THRESHOLD` (lower value = more sensitive)
- Reduce `GESTURE_STABLE_DURATION` for faster response

### Too many false triggers

- Increase `GESTURE_CONFIDENCE_THRESHOLD`
- Increase `GESTURE_STABLE_DURATION`
- Increase `GESTURE_COOLDOWN`

## Example Home Assistant Automation

```yaml
automation:
  - alias: "Turn on light with open palm"
    trigger:
      - platform: state
        entity_id: sensor.gesture_control
        to: "OPEN_PALM"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
  
  - alias: "Turn off light with closed fist"
    trigger:
      - platform: state
        entity_id: sensor.gesture_control
        to: "CLOSED_FIST"
    action:
      - service: light.turn_off
        target:
          entity_id: light.living_room
```

## Performance Optimization

The application is optimized for low-resource environments:

- Frame resolution reduced to 640x480
- Frame rate limited to 10 FPS
- Efficient MediaPipe model (lightweight)
- Single hand detection only

Typical resource usage:
- CPU: 50-80% of one core
- RAM: ~400-600 MB

## License

MIT License - Feel free to use and modify for your projects.

## Credits

- **MediaPipe**: Google's ML framework for hand tracking
- **OpenCV**: Computer vision library
- **Home Assistant**: Open-source home automation platform
