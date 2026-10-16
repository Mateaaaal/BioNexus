import textwrap

import matplotlib.patheffects as path_effects
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import pyqtSignal


class GelCanvas(FigureCanvasQTAgg):
    bands_modified = pyqtSignal()
    rename_requested = pyqtSignal(int)
    lane_clicked = pyqtSignal(int)  # New signal to transmit lane selection

    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)

        self.selected_lane_idx = None
        self.active_lane_x = None  # Tracks persistently selected lane
        self.lanes = []
        
        self.mpl_connect("button_press_event", self.on_press)
        self.mpl_connect("motion_notify_event", self.on_motion)
        self.mpl_connect("button_release_event", self.on_release)

    def on_press(self, event):
        if event.xdata is None or event.ydata is None:
            return

        click_x = event.xdata
        click_y = event.ydata

        tolerance_x = 15.0
        tolerance_y = 5.0

        closest_lane_idx = None
        min_dist_x = float("inf")

        for idx, lane_x in enumerate(self.lanes):
            dist = abs(click_x - lane_x)
            if dist < min_dist_x and dist < tolerance_x:
                min_dist_x = dist
                closest_lane_idx = idx

        if closest_lane_idx is None:
            return

        lane_key = self.lanes[closest_lane_idx]

        if lane_key not in self.raw_bands:
            self.raw_bands[lane_key] = []

        # Update active selection and broadcast signal
        self.active_lane_x = lane_key
        self.lane_clicked.emit(lane_key)

        if event.button == 1 and click_y < 0:
            if getattr(event, "dblclick", False):
                self.rename_requested.emit(lane_key)
                return
            else:
                self.selected_lane_idx = closest_lane_idx

        elif event.button == 3:
            img_height = self.current_image.shape[0]
            if click_y < 0 or click_y > img_height:
                return

            bands = self.raw_bands[lane_key]
            band_to_remove = None

            for i, pixel_y in enumerate(bands):
                if abs(click_y - pixel_y) < tolerance_y:
                    band_to_remove = i
                    break

            if band_to_remove is not None:
                bands.pop(band_to_remove)
            else:
                bands.append(click_y)
                bands.sort()

            self.bands_modified.emit()
            
        self.draw()  # Force redraw to show highlight

    def on_motion(self, event):
        if event.xdata is None or self.selected_lane_idx is None:
            return

        old_lane_x = self.lanes[self.selected_lane_idx]
        new_lane_x = int(event.xdata)

        if self.selected_lane_idx >= len(self.lanes):
            self.selected_lane_idx = None
            return

        if old_lane_x == new_lane_x:
            return

        for lane_x in self.lanes:
            if lane_x != old_lane_x and abs(new_lane_x - lane_x) < 3:
                return

        self.lanes[self.selected_lane_idx] = new_lane_x
        
        # Track active lane translation
        if self.active_lane_x == old_lane_x:
            self.active_lane_x = new_lane_x

        rebuilt_bands = {}
        for k, v in self.raw_bands.items():
            if k == old_lane_x:
                rebuilt_bands[new_lane_x] = v
            else:
                rebuilt_bands[k] = v

        self.raw_bands.clear()
        self.raw_bands.update(rebuilt_bands)

        rebuilt_names = {}
        for k, v in self.lane_names.items():
            if k == old_lane_x:
                rebuilt_names[new_lane_x] = v
            else:
                rebuilt_names[k] = v

        self.lane_names.clear()
        self.lane_names.update(rebuilt_names)

        self.bands_modified.emit()

    def on_release(self, event):
        self.selected_lane_idx = None

    def plot_gel(self, image, lanes, raw_bands, annotated_bands, lane_names, marker_lane_x):
        self.lanes = lanes
        self.current_image = image
        self.raw_bands = raw_bands
        self.annotated_bands = annotated_bands
        self.lane_names = lane_names
        self.marker_lane_x = marker_lane_x

        self.ax.clear()

        self.fig.patch.set_facecolor("#1E1E1E")
        self.ax.set_facecolor("#1E1E1E")

        self.ax.imshow(image, cmap="gray")
        self.ax.set_ylim(image.shape[0], -40)

        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_color("#8E8E93")
        self.ax.spines["bottom"].set_color("#8E8E93")
        self.ax.tick_params(colors="#8E8E93", labelsize=8)

        for i, lane_x in enumerate(lanes):
            default_name = f"L{i+1}"
            name = self.lane_names.get(lane_x, default_name)
            is_marker = lane_x == self.marker_lane_x
            is_active = lane_x == self.active_lane_x

            if name == default_name:
                text_angle = 0
                y_pos = -25
                display_name = name
            else:
                display_name = textwrap.fill(name, width=10)
                text_angle = 45
                y_pos = -40

            # Dynamic badge coloring
            if is_marker:
                bg_color = "#FFD60A"  # Yellow for marker
                text_color = "black"
            elif is_active:
                bg_color = "#64D2FF"  # Cyan for selected lane
                text_color = "black"
            else:
                bg_color = "#3A3A3C"  # Dark gray default
                text_color = "white"

            self.ax.text(
                lane_x,
                y_pos,
                f" {display_name} ",
                color=text_color,
                fontsize=8,
                fontweight="bold",
                ha="center",
                va="center",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor=bg_color,
                    edgecolor="none",
                    alpha=0.9,
                ),
                rotation=text_angle,
                clip_on=False,
            )

        for lane_x, bands in self.annotated_bands.items():
            is_marker = lane_x == self.marker_lane_x

            pixels = [item[0] for item in bands]
            self.ax.scatter(
                [lane_x] * len(pixels),
                pixels,
                facecolors="none",
                edgecolor="#FF3B30",
                linewidth=1.2,
                s=25,
                zorder=3,
            )

            for pixel_y, kda_val in bands:
                if kda_val is not None:
                    label = f"{kda_val} kDa" if is_marker else f"{kda_val}"
                else:
                    label = f"{int(pixel_y)}px" if is_marker else f"{int(pixel_y)}"

                self.ax.text(
                    lane_x + 6,
                    pixel_y,
                    label,
                    color="white",
                    fontsize=7,
                    fontweight="bold",
                    va="center",
                    path_effects=[
                        path_effects.withStroke(linewidth=2, foreground="black")
                    ],
                )
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.fig.tight_layout()
        self.draw()