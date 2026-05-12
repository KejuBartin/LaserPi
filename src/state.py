from dataclasses import asdict, dataclass, field, replace
from threading import Lock
import math
import random


@dataclass
class LaserState:
    effect_name: str = "static"
    effect_names: list[str] = field(default_factory=lambda: ["static"])
    motion_name: str = "none"
    motion_speed: float = 0.25
    motion_sync_to_bpm: bool = True
    motion_override_bpm: bool = False
    bounce_direction: str = "horizontal"
    bounce_range: float = 1.0
    shape_name: str = "square"
    # dvd effect speed multiplier (0.25, 0.5, 1.0)
    dvd_speed: float = 0.5
    color_name: str = "rainbow"
    bpm: float = 120.0
    rotation_speed: float = 90.0
    line_width: int = 6
    segments_per_edge: int = 100
    angle: float = 0.0
    beat_phase: float = 0.0
    scale: float = 1.0
    solid_color: str = "#ffffff"
    # output control
    output_enabled: bool = False

    # cropping as normalized fractions [0..1]
    crop_left: float = 0.0
    crop_right: float = 1.0
    crop_top: float = 0.0
    crop_bottom: float = 1.0

    # parallel lines effect parameters
    lines_count: int = 8
    lines_angle: float = 0.0
    line_angle: float = 0.0
    lines_offset: float = 0.0
    lines_gradient_zoom: float = 0.5
    viewport_width: int = 0
    viewport_height: int = 0
    
    # dots shape parameters
    dot_count: int = 5
    # shape size multiplier for circle, line, square, triangle
    shape_size: float = 1.0
    # bounce simulation state (normalized 0..1 across viewport)
    bounce_pos_x: float = 0.5
    bounce_pos_y: float = 0.5
    bounce_vx: float = 0.0
    bounce_vy: float = 0.0

    # dvd simulation state (normalized 0..1 across viewport)
    dvd_pos_x: float = 0.5
    dvd_pos_y: float = 0.5
    dvd_vx: float = 0.0
    dvd_vy: float = 0.0
    dvd_time: float = 0.0


class SharedLaserState:
    def __init__(self, initial_state=None):
        self._state = initial_state or LaserState()
        self._lock = Lock()

    def _copy_state(self):
        snapshot = replace(self._state)
        snapshot.effect_names = list(self._state.effect_names)
        return snapshot

    def snapshot(self):
        with self._lock:
            return self._copy_state()

    def snapshot_dict(self):
        with self._lock:
            return asdict(self._state)

    def update(self, **changes):
        with self._lock:
            for key, value in changes.items():
                if not hasattr(self._state, key):
                    continue

                if key == "effect_names":
                    names = [str(item) for item in value if str(item)]
                    self._state.effect_names = names
                    self._state.effect_name = names[0] if names else "static"
                    continue

                if key == "effect_name":
                    self._state.effect_name = str(value)
                    self._state.effect_names = [self._state.effect_name]
                    continue

                setattr(self._state, key, value)

            if not self._state.effect_names:
                self._state.effect_names = [self._state.effect_name]

            return self._copy_state()

    def advance_timing(self, dt):
        with self._lock:
            self._state.angle = (self._state.angle + self._state.rotation_speed * dt) % 360

            bpm = max(0.0, float(self._state.bpm))
            if bpm > 0:
                self._state.beat_phase = (self._state.beat_phase + dt * bpm / 60.0) % 1.0

            motion_name = getattr(self._state, "motion_name", "none")
            override_bpm = bool(getattr(self._state, "motion_override_bpm", False))
            effects = getattr(self._state, "effect_names", None) or [getattr(self._state, "effect_name", "static")]
            bounce_active = "bounce" in effects
            dvd_active = "dvd" in effects
            if motion_name != "none" or bounce_active or dvd_active:
                # Advance lines_offset continuously to avoid abrupt jumps when
                # external beat_phase updates occur (e.g. Ableton Link). Use the
                # current BPM as the rate for both override and synced modes so
                # motion stays smooth and infinite.
                speed = (max(0.0, float(self._state.bpm)) / 60.0) * max(0.0, float(self._state.motion_speed))
                step = speed * dt
                if motion_name in ("right-to-left", "bottom-to-top"):
                    step = -step
                self._state.lines_offset = (self._state.lines_offset + step) % 1.0

            # Bounce physics: maintain a normalized position and velocity in the
            # shared state and reflect on the 0..1 bounds so that the movement
            # behaves like a mirror (angle of incidence == angle of reflection).
            if bounce_active:
                # Initialize velocity if zero: pick a diagonal direction by
                # default, scaled by `motion_speed`. Use a random angle so
                # multiple restarts don't all bounce identically.
                if abs(self._state.bounce_vx) < 1e-9 and abs(self._state.bounce_vy) < 1e-9:
                    ang = random.random() * 2.0 * math.tau
                    self._state.bounce_vx = math.cos(ang) * float(self._state.motion_speed)
                    self._state.bounce_vy = math.sin(ang) * float(self._state.motion_speed)

                # Integrate position
                px = float(self._state.bounce_pos_x) + self._state.bounce_vx * dt
                py = float(self._state.bounce_pos_y) + self._state.bounce_vy * dt

                # Reflect on bounds [0..1]. Use a loop so a large step that
                # crosses multiple edges in one frame still resolves correctly
                # instead of jumping to the opposite side.
                while px < 0.0 or px > 1.0:
                    if px < 0.0:
                        px = -px
                        self._state.bounce_vx = -self._state.bounce_vx
                    elif px > 1.0:
                        px = 2.0 - px
                        self._state.bounce_vx = -self._state.bounce_vx

                while py < 0.0 or py > 1.0:
                    if py < 0.0:
                        py = -py
                        self._state.bounce_vy = -self._state.bounce_vy
                    elif py > 1.0:
                        py = 2.0 - py
                        self._state.bounce_vy = -self._state.bounce_vy

                self._state.bounce_pos_x = px
                self._state.bounce_pos_y = py

            if dvd_active:
                if abs(self._state.dvd_vx) < 1e-9 and abs(self._state.dvd_vy) < 1e-9:
                    ang = random.random() * 2.0 * math.tau
                    self._state.dvd_vx = math.cos(ang)
                    self._state.dvd_vy = math.sin(ang)

                # Scale DVD speed by BPM so the BPM slider controls motion speed.
                # dvd_speed acts as a multiplier on top of the BPM-derived speed.
                bpm = max(0.0, float(self._state.bpm))
                speed = (bpm / 60.0) * max(0.0, float(self._state.dvd_speed))
                self._state.dvd_time += dt * speed
                px = float(self._state.dvd_pos_x) + self._state.dvd_vx * speed * dt
                py = float(self._state.dvd_pos_y) + self._state.dvd_vy * speed * dt

                while px < 0.0 or px > 1.0:
                    if px < 0.0:
                        px = -px
                        self._state.dvd_vx = -self._state.dvd_vx
                    elif px > 1.0:
                        px = 2.0 - px
                        self._state.dvd_vx = -self._state.dvd_vx

                while py < 0.0 or py > 1.0:
                    if py < 0.0:
                        py = -py
                        self._state.dvd_vy = -self._state.dvd_vy
                    elif py > 1.0:
                        py = 2.0 - py
                        self._state.dvd_vy = -self._state.dvd_vy

                self._state.dvd_pos_x = px
                self._state.dvd_pos_y = py

            return self._copy_state()
