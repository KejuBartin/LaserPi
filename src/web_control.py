import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from colors import list_color_names, parse_hex_color
from effects import list_effect_names, list_motion_names
from shapes import list_shape_names


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LaserPi Control</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #081018;
      --panel: #0f1b29;
      --panel-2: #142235;
      --text: #edf4ff;
      --muted: #96a6bb;
      --accent: #61dafb;
      --accent-2: #8ef0b5;
      --border: rgba(255, 255, 255, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "SF Pro Display", "Avenir Next", "Trebuchet MS", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(97, 218, 251, 0.12), transparent 30%),
        radial-gradient(circle at bottom right, rgba(142, 240, 181, 0.10), transparent 25%),
        var(--bg);
      color: var(--text);
    }
    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px;
    }
    .hero {
      display: grid;
      gap: 12px;
      margin-bottom: 20px;
    }
    .hero h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.2rem);
      letter-spacing: -0.04em;
    }
    .hero p { margin: 0; color: var(--muted); max-width: 70ch; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
    }
    .card {
      background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px;
      backdrop-filter: blur(10px);
    }
    .card h2 {
      margin: 0 0 12px;
      font-size: 1rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }
    .choices {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    button, input {
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      border-radius: 999px;
      padding: 10px 14px;
      font: inherit;
    }
    button, select, input[type="range"], input[type="color"], input[type="number"] {
      cursor: pointer;
    }
    button.active {
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: #061018;
      border-color: transparent;
      font-weight: 700;
    }
    .field {
      display: grid;
      gap: 8px;
    }
    .field.inline {
      grid-template-columns: auto 1fr auto;
      align-items: center;
    }
    label { color: var(--muted); font-size: 0.92rem; }
    input[type="range"] { width: 100%; padding: 10px 0; }
    input[type="color"] {
      width: 100%;
      height: 44px;
      padding: 4px;
      border-radius: 14px;
    }
    select {
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      border-radius: 999px;
      padding: 10px 14px;
      font: inherit;
      width: 100%;
    }
    .value {
      color: var(--text);
      font-variant-numeric: tabular-nums;
      min-width: 4ch;
      text-align: right;
    }
    .hidden { display: none; }
    .state {
      display: grid;
      gap: 8px;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 0.92rem;
      background: var(--panel-2);
      padding: 14px;
      border-radius: 14px;
      overflow: auto;
    }
  </style>
</head>
<body>
  <main>
    <div class="hero">
      <h1>LaserPi Control</h1>
      <p>Pick a shape, effect, and palette from the LAN. This dashboard talks to the same shared state that the renderer uses, so BPM or OSC can hook into it later without changing the drawing code.</p>
    </div>
    <div class="grid">
      <section class="card">
        <h2>Shape</h2>
        <div class="choices" id="shapes"></div>
        <div class="field" id="line_style_controls">
          <label for="line_width">Thickness</label>
          <input id="line_width" type="range" min="1" max="40" step="1">
          <input id="line_width_value" type="number" min="1" max="40" step="1">
        </div>
        <div class="field hidden" id="line_controls">
          <label for="line_angle">Line Angle</label>
          <input id="line_angle" type="range" min="0" max="360" step="1">
          <input id="line_angle_value" type="number" min="0" max="360" step="1">
          <button id="line_angle_reset" type="button">Reset Angle</button>
        </div>
        <div class="field hidden" id="multilines_controls">
          <label for="lines_count">Parallel Lines</label>
          <input id="lines_count" type="range" min="1" max="64" step="1">
          <input id="lines_count_value" type="number" min="1" max="64" step="1">
          <label for="lines_angle">Angle</label>
          <input id="lines_angle" type="range" min="0" max="360" step="1">
          <input id="lines_angle_value" type="number" min="0" max="360" step="1">
          <label for="lines_gradient_zoom">Gradient Zoom</label>
          <input id="lines_gradient_zoom" type="range" min="0.1" max="4" step="0.05">
          <input id="lines_gradient_zoom_value" type="number" min="0.1" max="4" step="0.05">
        </div>
        <div class="field hidden" id="dots_controls">
          <label for="dot_count">Dot Count</label>
          <input id="dot_count" type="range" min="1" max="50" step="1">
          <input id="dot_count_value" type="number" min="1" max="50" step="1">
        </div>
        <div class="field hidden" id="shape_size_controls">
          <label for="shape_size">Size</label>
          <input id="shape_size" type="range" min="0.1" max="3.0" step="0.1">
          <input id="shape_size_value" type="number" min="0.1" max="3.0" step="0.1">
        </div>
      </section>
      <section class="card">
        <h2>Effect</h2>
        <div class="choices" id="effects"></div>
        <div class="field">
          <label>Selection</label>
          <div class="value" id="effect_summary"></div>
        </div>
        <div class="field">
          <label for="motion_effect">Motion</label>
          <select id="motion_effect"></select>
          <label for="bounce_direction" id="bounce_direction_label" class="hidden">Bounce Direction</label>
          <select id="bounce_direction" class="hidden">
            <option value="horizontal">Horizontal</option>
            <option value="vertical">Vertical</option>
          </select>
          <label for="bounce_range" id="bounce_range_label" class="hidden">Bounce Space</label>
          <input id="bounce_range" class="hidden" type="range" min="0" max="1" step="0.01">
          <input id="bounce_range_value" class="hidden" type="number" min="0" max="1" step="0.01">
          <label for="dvd_speed" id="dvd_speed_label" class="hidden">DVD Speed</label>
          <select id="dvd_speed" class="hidden">
            <option value="0.25">0.25x</option>
            <option value="0.5" selected>0.5x</option>
            <option value="1.0">1.0x</option>
          </select>
        </div>
      </section>
      <section class="card">
        <h2>Palette</h2>
        <div class="choices" id="colors"></div>
        <div class="field">
          <label for="solid_color">Solid Color</label>
          <input id="solid_color" type="color" value="#ffffff">
        </div>
      </section>
      <section class="card">
        <h2>Timing</h2>
        <div class="field inline">
          <label for="bpm">BPM</label>
          <input id="bpm" type="range" min="40" max="220" step="1">
          <span class="value" id="bpm_value"></span>
        </div>
        <div class="field">
          <label for="motion_override_bpm">Motion Timing</label>
          <select id="motion_override_bpm">
            <option value="music">Follow Music Beat</option>
            <option value="bpm">Override Beat (Use BPM Slider)</option>
          </select>
        </div>
        <div class="field">
          <label for="rotation_speed">Rotation speed</label>
          <input id="rotation_speed" type="range" min="0" max="360" step="1">
        </div>
      </section>
      <section class="card">
        <h2>Output</h2>
        <div class="field">
          <label>Enabled</label>
          <button id="output_toggle">Toggle</button>
        </div>
        <div class="field">
          <label for="crop_left">Crop Left</label>
          <input id="crop_left" type="range" min="0" max="1" step="0.01">
        </div>
        <div class="field">
          <label for="crop_right">Crop Right</label>
          <input id="crop_right" type="range" min="0" max="1" step="0.01">
        </div>
        <div class="field">
          <label for="crop_top">Crop Top</label>
          <input id="crop_top" type="range" min="0" max="1" step="0.01">
        </div>
        <div class="field">
          <label for="crop_bottom">Crop Bottom</label>
          <input id="crop_bottom" type="range" min="0" max="1" step="0.01">
        </div>
      </section>
      <section class="card" style="grid-column: 1 / -1;">
        <h2>Current State</h2>
        <pre class="state" id="state"></pre>
      </section>
    </div>
  </main>
  <script>
    const stateView = document.getElementById('state');
    const bpmValue = document.getElementById('bpm_value');
    const bpmInput = document.getElementById('bpm');
    const rotationInput = document.getElementById('rotation_speed');
    const outputToggle = document.getElementById('output_toggle');
    const solidColor = document.getElementById('solid_color');
    const cropLeft = document.getElementById('crop_left');
    const cropRight = document.getElementById('crop_right');
    const cropTop = document.getElementById('crop_top');
    const cropBottom = document.getElementById('crop_bottom');
    const lineControls = document.getElementById('line_controls');
    const multilinesControls = document.getElementById('multilines_controls');
    const lineAngle = document.getElementById('line_angle');
    const lineAngleValue = document.getElementById('line_angle_value');
    const lineAngleReset = document.getElementById('line_angle_reset');
    const linesCount = document.getElementById('lines_count');
    const linesCountValue = document.getElementById('lines_count_value');
    const linesAngle = document.getElementById('lines_angle');
    const linesAngleValue = document.getElementById('lines_angle_value');
    const lineWidth = document.getElementById('line_width');
    const lineWidthValue = document.getElementById('line_width_value');
    const motionEffect = document.getElementById('motion_effect');
    const linesGradientZoom = document.getElementById('lines_gradient_zoom');
    const linesGradientZoomValue = document.getElementById('lines_gradient_zoom_value');
    const dotsControls = document.getElementById('dots_controls');
    const dotCount = document.getElementById('dot_count');
    const dotCountValue = document.getElementById('dot_count_value');
    const shapeSizeControls = document.getElementById('shape_size_controls');
    const shapeSize = document.getElementById('shape_size');
    const shapeSizeValue = document.getElementById('shape_size_value');
    const bounceDirection = document.getElementById('bounce_direction');
    const bounceDirectionLabel = document.getElementById('bounce_direction_label');
    const bounceRange = document.getElementById('bounce_range');
    const bounceRangeValue = document.getElementById('bounce_range_value');
    const bounceRangeLabel = document.getElementById('bounce_range_label');
    const dvdSpeed = document.getElementById('dvd_speed');
    const dvdSpeedLabel = document.getElementById('dvd_speed_label');
    const motionOverrideBpm = document.getElementById('motion_override_bpm');
    const effectSummary = document.getElementById('effect_summary');
    const dvdSpeedOptions = ['0.25', '0.5', '1.0'];
    let solidColorTimer = null;

    function normalizeDvdSpeedValue(value) {
      const numeric = Number(value);
      if (!Number.isFinite(numeric)) {
        return '0.5';
      }

      let closest = dvdSpeedOptions[0];
      let smallestDistance = Infinity;
      for (const option of dvdSpeedOptions) {
        const distance = Math.abs(Number(option) - numeric);
        if (distance < smallestDistance) {
          smallestDistance = distance;
          closest = option;
        }
      }
      return closest;
    }

    const options = {
      effects: document.getElementById('effects'),
      shapes: document.getElementById('shapes'),
      colors: document.getElementById('colors'),
    };

    async function request(url, method = 'GET', body = null) {
      const response = await fetch(url, {
        method,
        headers: body ? {'Content-Type': 'application/json'} : undefined,
        body: body ? JSON.stringify(body) : null,
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      return response.json();
    }

    async function apply(update) {
      await request('/api/state', 'POST', update);
      await refresh();
    }

    function renderSelect(target, items, activeValue) {
      target.innerHTML = '';
      items.forEach((item) => {
        const option = document.createElement('option');
        option.value = item;
        option.textContent = item;
        if (item === activeValue) {
          option.selected = true;
        }
        target.appendChild(option);
      });
    }

    function renderButtons(target, items, activeValues, key, multiSelect = false) {
      target.innerHTML = '';
      items.forEach((item) => {
        const button = document.createElement('button');
        button.textContent = item;
        button.className = activeValues.includes(item) ? 'active' : '';
        button.addEventListener('click', async () => {
          if (!multiSelect) {
            await apply({[key]: item});
            return;
          }

          const selected = new Set(activeValues);
          if (selected.has(item)) {
            selected.delete(item);
          } else {
            selected.add(item);
          }

          await apply({[key]: Array.from(selected)});
        });
        target.appendChild(button);
      });
    }

    async function refresh() {
      const meta = await request('/api/meta');
      const state = await request('/api/state');

      renderButtons(options.effects, meta.effects, state.effect_names || [state.effect_name], 'effect_names', true);
      renderSelect(motionEffect, ['none', ...(meta.motions || [])], state.motion_name || 'none');
      renderButtons(options.shapes, meta.shapes, [state.shape_name], 'shape');
      renderButtons(options.colors, meta.colors, [state.color_name], 'color');

      bpmInput.value = state.bpm;
      bpmValue.textContent = `${Math.round(state.bpm)}`;
      rotationInput.value = state.rotation_speed;
      outputToggle.textContent = state.output_enabled ? 'On' : 'Off';
      solidColor.value = state.solid_color || '#ffffff';
      cropLeft.value = state.crop_left;
      cropRight.value = state.crop_right;
      cropTop.value = state.crop_top;
      cropBottom.value = state.crop_bottom;
      linesCount.value = state.lines_count;
      linesCountValue.value = state.lines_count;
      linesAngle.value = state.lines_angle;
      linesAngleValue.value = Math.round(state.lines_angle);
      lineAngle.value = state.line_angle ?? 0;
      lineAngleValue.value = Math.round(state.line_angle ?? 0);
      lineWidth.value = state.line_width;
      lineWidthValue.value = state.line_width;
      motionOverrideBpm.value = (state.motion_override_bpm ?? false) ? 'bpm' : 'music';
      linesGradientZoom.value = state.lines_gradient_zoom ?? 0.5;
      linesGradientZoomValue.value = (state.lines_gradient_zoom ?? 0.5).toFixed(2);
      lineControls.classList.toggle('hidden', state.shape_name !== 'line');
      multilinesControls.classList.toggle('hidden', state.shape_name !== 'multilines');
      dotsControls.classList.toggle('hidden', state.shape_name !== 'dots');
      dotCount.value = state.dot_count ?? 5;
      dotCountValue.value = state.dot_count ?? 5;
      const shapeHasSize = ['circle', 'line', 'square', 'triangle'].includes(state.shape_name);
      shapeSizeControls.classList.toggle('hidden', !shapeHasSize);
      shapeSize.value = state.shape_size ?? 1.0;
      shapeSizeValue.value = Number(state.shape_size ?? 1.0).toFixed(1);
      const bounceActive = !!(state.effect_names?.includes('bounce') || state.effect_name === 'bounce');
      bounceDirection.value = state.bounce_direction ?? 'horizontal';
      bounceDirection.classList.toggle('hidden', !bounceActive);
      bounceDirectionLabel.classList.toggle('hidden', !bounceActive);
      bounceRange.value = state.bounce_range ?? 1.0;
      bounceRangeValue.value = Number(state.bounce_range ?? 1.0).toFixed(2);
      bounceRange.classList.toggle('hidden', !bounceActive);
      bounceRangeValue.classList.toggle('hidden', !bounceActive);
      bounceRangeLabel.classList.toggle('hidden', !bounceActive);
      effectSummary.textContent = [
        ...(state.effect_names && state.effect_names.length ? state.effect_names : [state.effect_name]),
        ...(state.motion_name && state.motion_name !== 'none' ? [state.motion_name] : []),
      ].join(', ');
      stateView.textContent = JSON.stringify(state, null, 2);
        const dvdActive = !!(state.effect_names?.includes('dvd') || state.effect_name === 'dvd');
        dvdSpeed.value = normalizeDvdSpeedValue(state.dvd_speed ?? 0.5);
        dvdSpeed.classList.toggle('hidden', !dvdActive);
        dvdSpeedLabel.classList.toggle('hidden', !dvdActive);
    }

    bpmInput.addEventListener('input', () => {
      bpmValue.textContent = `${Math.round(Number(bpmInput.value))}`;
    });
    bpmInput.addEventListener('change', () => apply({bpm: Number(bpmInput.value)}));
    rotationInput.addEventListener('change', () => apply({rotation_speed: Number(rotationInput.value)}));

    outputToggle.addEventListener('click', async () => {
      const s = await request('/api/state');
      apply({output_enabled: !s.output_enabled});
    });

    solidColor.addEventListener('input', () => {
      clearTimeout(solidColorTimer);
      solidColorTimer = setTimeout(() => apply({color_name: 'solid', solid_color: solidColor.value}), 80);
    });
    solidColor.addEventListener('change', () => {
      clearTimeout(solidColorTimer);
      apply({color_name: 'solid', solid_color: solidColor.value});
    });

    cropLeft.addEventListener('change', () => apply({crop_left: Number(cropLeft.value)}));
    cropRight.addEventListener('change', () => apply({crop_right: Number(cropRight.value)}));
    cropTop.addEventListener('change', () => apply({crop_top: Number(cropTop.value)}));
    cropBottom.addEventListener('change', () => apply({crop_bottom: Number(cropBottom.value)}));

    linesCount.addEventListener('input', () => {
      linesCountValue.value = Number(linesCount.value);
    });
    linesCount.addEventListener('change', () => apply({lines_count: Number(linesCount.value)}));
    linesCountValue.addEventListener('change', () => apply({lines_count: Number(linesCountValue.value)}));

    linesAngle.addEventListener('input', () => {
      linesAngleValue.value = Math.round(Number(linesAngle.value));
    });
    linesAngle.addEventListener('change', () => apply({lines_angle: Number(linesAngle.value)}));
    linesAngleValue.addEventListener('change', () => apply({lines_angle: Number(linesAngleValue.value)}));

    lineAngle.addEventListener('input', () => {
      lineAngleValue.value = Math.round(Number(lineAngle.value));
    });
    lineAngle.addEventListener('change', () => apply({line_angle: Number(lineAngle.value)}));
    lineAngleValue.addEventListener('change', () => apply({line_angle: Number(lineAngleValue.value)}));
    lineAngleReset.addEventListener('click', () => apply({line_angle: 0}));

    lineWidth.addEventListener('input', () => {
      lineWidthValue.value = Number(lineWidth.value);
    });
    lineWidth.addEventListener('change', () => apply({line_width: Number(lineWidth.value)}));
    lineWidthValue.addEventListener('change', () => apply({line_width: Number(lineWidthValue.value)}));

    motionEffect.addEventListener('change', () => apply({motion_name: motionEffect.value}));
    motionOverrideBpm.addEventListener('change', () => apply({motion_override_bpm: motionOverrideBpm.value === 'bpm'}));
    linesGradientZoom.addEventListener('input', () => {
      linesGradientZoomValue.value = Number(linesGradientZoom.value).toFixed(2);
    });
    linesGradientZoom.addEventListener('change', () => apply({lines_gradient_zoom: Number(linesGradientZoom.value)}));
    linesGradientZoomValue.addEventListener('change', () => apply({lines_gradient_zoom: Number(linesGradientZoomValue.value)}));

    dotCount.addEventListener('input', () => {
      dotCountValue.value = Number(dotCount.value);
    });
    dotCount.addEventListener('change', () => apply({dot_count: Number(dotCount.value)}));
    dotCountValue.addEventListener('change', () => apply({dot_count: Number(dotCountValue.value)}));

    shapeSize.addEventListener('input', () => {
      shapeSizeValue.value = Number(shapeSize.value).toFixed(1);
    });
    shapeSize.addEventListener('change', () => apply({shape_size: Number(shapeSize.value)}));
    shapeSizeValue.addEventListener('change', () => apply({shape_size: Number(shapeSizeValue.value)}));

    bounceDirection.addEventListener('change', () => apply({bounce_direction: bounceDirection.value}));
    bounceRange.addEventListener('input', () => {
      bounceRangeValue.value = Number(bounceRange.value).toFixed(2);
    });
    bounceRange.addEventListener('change', () => apply({bounce_range: Number(bounceRange.value)}));
    bounceRangeValue.addEventListener('change', () => apply({bounce_range: Number(bounceRangeValue.value)}));

    dvdSpeed.addEventListener('change', () => apply({dvd_speed: Number(dvdSpeed.value)}));

    refresh();
  </script>
</body>
</html>
"""


MAX_REQUEST_BYTES = 16 * 1024
MAX_BPM = 300.0
MAX_ROTATION_SPEED = 720.0
MAX_LINE_WIDTH = 40
MAX_SEGMENTS_PER_EDGE = 200
MAX_LINES_COUNT = 64
MAX_DOT_COUNT = 50


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
    return bool(value)


def _build_handler(control_state):
    class LaserControlHandler(BaseHTTPRequestHandler):
        def _send_json(self, payload, status=200):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, payload):
            body = payload.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self):
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > MAX_REQUEST_BYTES:
                raise ValueError("Request body is too large")
            raw = self.rfile.read(content_length)
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))

        def _apply_state_update(self, payload):
            updates = {}

            if "effect" in payload:
                effect_name = str(payload["effect"])
                if effect_name not in list_effect_names():
                    raise ValueError(f"Unknown effect: {effect_name}")
                updates["effect_name"] = effect_name
                updates["effect_names"] = [effect_name]

            if "effect_names" in payload:
                effect_names = [str(item) for item in payload["effect_names"] if str(item)]
                invalid = [name for name in effect_names if name not in list_effect_names()]
                if invalid:
                    raise ValueError(f"Unknown effect(s): {', '.join(invalid)}")
                updates["effect_names"] = effect_names

            if "shape" in payload:
                shape_name = str(payload["shape"])
                if shape_name not in list_shape_names():
                    raise ValueError(f"Unknown shape: {shape_name}")
                updates["shape_name"] = shape_name

            if "color" in payload:
                color_name = str(payload["color"])
                if color_name not in list_color_names():
                    raise ValueError(f"Unknown color palette: {color_name}")
                updates["color_name"] = color_name

            if "bpm" in payload:
                updates["bpm"] = max(0.0, min(MAX_BPM, float(payload["bpm"])))

            if "rotation_speed" in payload:
                updates["rotation_speed"] = max(0.0, min(MAX_ROTATION_SPEED, float(payload["rotation_speed"])))

            if "motion_name" in payload:
                motion_name = str(payload["motion_name"])
                if motion_name != "none" and motion_name not in list_motion_names():
                    raise ValueError(f"Unknown motion effect: {motion_name}")
                updates["motion_name"] = motion_name

            if "motion_speed" in payload:
                updates["motion_speed"] = max(0.0, float(payload["motion_speed"]))
            if "motion_override_bpm" in payload:
                updates["motion_override_bpm"] = _parse_bool(payload["motion_override_bpm"])
            if "motion_sync_to_bpm" in payload:
                # Backward compatibility: old flag meant BPM-linked motion.
                updates["motion_override_bpm"] = _parse_bool(payload["motion_sync_to_bpm"])

            if "output_enabled" in payload:
                updates["output_enabled"] = _parse_bool(payload["output_enabled"])

            if "solid_color" in payload:
                solid_color = str(payload["solid_color"])
                parse_hex_color(solid_color)
                updates["solid_color"] = solid_color

            # crop values: normalized 0..1
            for key in ("crop_left", "crop_right", "crop_top", "crop_bottom"):
                if key in payload:
                    v = float(payload[key])
                    updates[key] = max(0.0, min(1.0, v))

            # lines shape params
            if "lines_count" in payload:
                updates["lines_count"] = max(1, min(MAX_LINES_COUNT, int(payload["lines_count"])))
            if "lines_angle" in payload:
                updates["lines_angle"] = float(payload["lines_angle"]) % 360.0
            if "line_angle" in payload:
                updates["line_angle"] = float(payload["line_angle"]) % 360.0
            if "lines_speed" in payload:
                updates["motion_speed"] = max(0.0, float(payload["lines_speed"]))
            if "lines_mode" in payload:
                motion_name = str(payload["lines_mode"])
                if motion_name != "rotate" and motion_name not in list_motion_names():
                    raise ValueError(f"Unknown motion effect: {motion_name}")
                updates["motion_name"] = motion_name if motion_name != "rotate" else "none"
            if "lines_gradient_zoom" in payload:
                updates["lines_gradient_zoom"] = max(0.01, min(4.0, float(payload["lines_gradient_zoom"])))

            if "dot_count" in payload:
                updates["dot_count"] = max(1, min(MAX_DOT_COUNT, int(payload["dot_count"])))
            if "bounce_direction" in payload:
                updates["bounce_direction"] = str(payload["bounce_direction"])
            if "bounce_range" in payload:
                updates["bounce_range"] = max(0.0, min(1.0, float(payload["bounce_range"])))
            if "dvd_speed" in payload:
                updates["dvd_speed"] = max(0.0, float(payload["dvd_speed"]))
            if "shape_size" in payload:
                updates["shape_size"] = max(0.1, min(3.0, float(payload["shape_size"])))

            if "line_width" in payload:
                updates["line_width"] = max(1, min(MAX_LINE_WIDTH, int(payload["line_width"])))

            if "segments_per_edge" in payload:
                updates["segments_per_edge"] = max(1, min(MAX_SEGMENTS_PER_EDGE, int(payload["segments_per_edge"])))

            if "scale" in payload:
                updates["scale"] = max(0.1, float(payload["scale"]))

            control_state.update(**updates)

        def do_GET(self):
            if self.path == "/":
                return self._send_html(HTML)

            if self.path == "/api/meta":
                return self._send_json(
                    {
                        "effects": list_effect_names(),
                        "motions": list_motion_names(),
                        "shapes": list_shape_names(),
                        "colors": list_color_names(),
                    }
                )

            if self.path == "/api/state":
                return self._send_json(control_state.snapshot_dict())

            self.send_error(404, "Not found")

        def do_POST(self):
            if self.path != "/api/state":
                self.send_error(404, "Not found")
                return

            try:
                payload = self._read_json()
                self._apply_state_update(payload)
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_error(400, str(exc))
                return

            self._send_json(control_state.snapshot_dict())

        def log_message(self, format, *args):
            del format, args

    return LaserControlHandler


def start_web_server(control_state, host="0.0.0.0", port=8080):
    server = ThreadingHTTPServer((host, port), _build_handler(control_state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
