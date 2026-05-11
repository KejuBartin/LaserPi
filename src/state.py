from dataclasses import asdict, dataclass, field, replace
from threading import Lock


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


class SharedLaserState:
    def __init__(self, initial_state=None):
        self._state = initial_state or LaserState()
        self._lock = Lock()

    def snapshot(self):
        with self._lock:
            return replace(self._state)

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

            return replace(self._state)

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
            if motion_name != "none" or bounce_active:
                if override_bpm:
                    speed = max(0.0, float(self._state.bpm)) / 60.0
                    step = speed * dt
                    if motion_name in ("right-to-left", "bottom-to-top"):
                        step = -step
                    self._state.lines_offset = (self._state.lines_offset + step) % 1.0
                else:
                    phase = self._state.beat_phase % 1.0
                    if motion_name in ("right-to-left", "bottom-to-top"):
                        phase = (-phase) % 1.0
                    self._state.lines_offset = phase

            return replace(self._state)