#!/usr/bin/env python3
# viewer.py – interactive A‑Scan viewer (rev‑7: label polish)

import os
import sys
import numpy as np
import h5py
import matplotlib
print(matplotlib.__version__)
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RangeSlider
import matplotlib.image as mpimg

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QAction, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QMessageBox
)


class ScanViewer(QMainWindow):
    # ------------------------------------------------------------------ #
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A‑Scan viewer")
        self.resize(1100, 750)

        # -------------------- Dashboard -------------------------------- #
        self.hover_lbl     = QLabel("Hover: (x=?, y=?)")
        self.selected_lbl  = QLabel("Selected: (x=?, y=?)")
        self.idx_range_lbl = QLabel("Idx 1‑625")
        self.amp_range_lbl = QLabel("Amp 0‑?")

        self.analysis_cmb = QComboBox()
        self.analysis_cmb.addItems(["basic", "radius 1 average"])
        self.analysis_cmb.currentTextChanged.connect(self._on_analysis_change)


        dash = QWidget();  dash_lay = QHBoxLayout(dash)
        dash_lay.setContentsMargins(6, 2, 6, 2);  dash_lay.setSpacing(12)
        for w in (self.hover_lbl, self.selected_lbl,
                  self.idx_range_lbl, self.amp_range_lbl):
            w.setMinimumWidth(110); dash_lay.addWidget(w)
        dash_lay.addWidget(QLabel("Analysis:")); dash_lay.addWidget(self.analysis_cmb)
        dash_lay.addStretch(1)

        # -------------------- Blank figure prompt ---------------------- #
        self.fig = Figure(facecolor="#e0e0e0"); self.canvas = FigureCanvas(self.fig)
        self._build_blank_prompt()

        # -------------------- Central widget --------------------------- #
        central = QWidget(); vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0); vbox.setSpacing(0)
        vbox.addWidget(dash, 0); vbox.addWidget(self.canvas, 1)
        self.setCentralWidget(central)

        # -------------------- Menu ------------------------------------ #
        file_menu = self.menuBar().addMenu("&File")
        open_act = QAction("&Open…", self); open_act.triggered.connect(self.open_file)
        self.export_act = QAction("&Export Image…", self); self.export_act.setEnabled(False)
        self.export_act.triggered.connect(self.export_image)
        file_menu.addAction(open_act); file_menu.addAction(self.export_act)

        # -------------------- State holders --------------------------- #
        self.vectors = None; self.global_min = self.global_max = None
        self.global_amp_max = None; self.last_x = self.last_y = None
        self.current_filename = None; self.current_gray = None
        self.img_handle = None; self.idx_vline_low = self.idx_vline_high = None

    # ------------------------------------------------------------------ #
    def _style_slider(self, slider, label_left=None, label_right=None):
        slider.label.set_visible(False)
        slider.valtext.set_visible(False)
        slider.ax.margins(x=0)
        slider.ax.set_yticks([])

        # --- remove any previous side‑labels we added ---
        for t in list(slider.ax.texts):
            if getattr(t, "_side_label", False):
                t.remove()


        # If either label is present, shrink the track
        if label_left or label_right:
            if not hasattr(slider.ax, "_orig_pos"):
                slider.ax._orig_pos = slider.ax.get_position()
            box = slider.ax._orig_pos
            # box = slider.ax.get_position()
            slider.ax.set_position([
                box.x0 + 0.06,  # shift right (left margin)
                box.y0,
                box.width - 0.12,  # shrink width (room for both sides)
                box.height
            ])
        # else:
        #     slider.valtext.set_visible(False)

        if label_left:
            txt = slider.ax.text(-0.03, 0.5, label_left,
                                 ha='right', va='center', fontsize=9,
                                 transform=slider.ax.transAxes)
            txt._side_label = True  # mark for future cleanup

        if label_right:
            txt = slider.ax.text(1.03, 0.5, label_right,
                                 ha='left', va='center', fontsize=9,
                                 transform=slider.ax.transAxes)
            txt._side_label = True

    # ------------------------------------------------------------------ #

    def _build_blank_prompt(self):
        self.fig.clf(); ax = self.fig.add_subplot(111); ax.set_axis_off()
        ax.text(0.5, 0.5, "File ▸ Open… to load data",
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        self.canvas.draw_idle()

    # ------------------------------------------------------------------ #
    def _add_slider_label(self, slider, text, where='top'):
        """Center a label relative to a RangeSlider."""
        slider.label.set_visible(False)      # hide default label
        slider.valtext.set_visible(False)    # hide (min,max) readout
        if where == 'top':
            y, va = 1.08, 'bottom'
        else:  # 'bot'
            y, va = -0.25, 'top'
        slider.ax.text(0.5, y, text, ha='center', va=va,
                       transform=slider.ax.transAxes, fontsize=9)

    # ------------------------------------------------------------------ #
    def _setup_full_layout(self):
        self.fig.clf()
        self.fig.subplots_adjust(left=0.08, right=0.96,
                         top=0.97, bottom=0.12, hspace=0.07)
        gs = self.fig.add_gridspec(4, 1, height_ratios=[4, 0.6, 3, 0.6])

        self.ax_image      = self.fig.add_subplot(gs[0, 0]); self.ax_image.set_axis_off()
        self.ax_amp_slider = self.fig.add_subplot(gs[1, 0])
        self.ax_line       = self.fig.add_subplot(gs[2, 0])
        self.ax_idx_slider = self.fig.add_subplot(gs[3, 0])


        self.amp_slider = RangeSlider(self.ax_amp_slider, "",
                                      0.0, 1.0, valinit=(0.0, 1.0))

        self.idx_slider = RangeSlider(self.ax_idx_slider, "",
                                      1, 625, valinit=(1, 625), valstep=1)
        self._style_slider(self.amp_slider,
                           label_left="0.0",
                           label_right="1.0")

        self._style_slider(self.idx_slider)


        self.amp_slider.on_changed(self._on_amp_change)
        self.idx_slider.on_changed(self._on_idx_change)

        # initial prompt in signal area
        self.ax_line.set_xlabel("Sample index")
        self.ax_line.set_ylabel("Amplitude")
        self.ax_line.text(0.5, 0.5, "Click a pixel to display signal",
                          ha='center', va='center', transform=self.ax_line.transAxes,
                          fontsize=12)

        low_idx, high_idx = map(int, self.idx_slider.val)
        self.idx_vline_low  = self.ax_line.axvline(low_idx,  color='red', lw=0.8)
        self.idx_vline_high = self.ax_line.axvline(high_idx, color='red', lw=0.8)

        # mpl events
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("button_press_event", self._on_click)

    # ------------------------------------------------------------------ #
    def open_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Open HDF/HDF5 file", "", "HDF files (*.hdf *.h5 *.hdf5)")
        if not fname: return

        with h5py.File(fname, "r") as f:
            if "A-Scans" not in f:
                QMessageBox.warning(self, "Error", "Dataset 'A-Scans' not found"); return
            data = f["A-Scans"][...]
        if data.shape != (18130, 625):
            QMessageBox.warning(self, "Error", f"Unexpected dataset shape {data.shape}"); return


        raw = data.reshape((74, 245, 625), order="C")
        self.vectors_raw = raw #temporarily store the raw data

        # ---- radius-1 neighbour average (raw units) ----
        pad = np.pad(raw, ((1, 1), (1, 1), (0, 0)), mode='edge')
        self.vectors_avg_raw = (
                                       pad[0:-2, 0:-2] + pad[0:-2, 1:-1] + pad[0:-2, 2:] +
                                       pad[1:-1, 0:-2] + pad[1:-1, 1:-1] + pad[1:-1, 2:] +
                                       pad[2:, 0:-2] + pad[2:, 1:-1] + pad[2:, 2:]
                               ) / 9.0  # shape 74×245×625

        # ---- normalise each cube separately for plotting ----
        def normalise(cube):
            vmin = cube.min(axis=2, keepdims=True)
            vmax = cube.max(axis=2, keepdims=True)
            span = np.maximum(vmax - vmin, 1e-6)
            return (cube - vmin) / span

        self.vectors = normalise(self.vectors_raw)
        self.vectors_avg = normalise(self.vectors_avg_raw)

        # vmin = raw.min(axis=2, keepdims=True)
        # vmax = raw.max(axis=2, keepdims=True)
        # span = np.maximum(vmax - vmin, 1e-6)

        # default view = basic
        self.active_raw = self.vectors_raw
        self.active_norm = self.vectors
        self.global_amp_max = float((self.active_raw.max(axis=2) -
                                     self.active_raw.min(axis=2)).max())

        # # Normalize to 0–1 range
        # self.vectors = (raw - vmin) / span  # now normalized to 0–1
        # self.global_min = 0.0
        # self.global_max = 1.0
        # # self.global_amp_max = 1.0
        # self.global_amp_max = float((raw.max(axis=2) - raw.min(axis=2)).max())

        self.current_filename = fname

        self.img_handle = None
        self._setup_full_layout()
        self._update_image(); self._update_dash_labels()
        self.last_x = self.last_y = None; self.export_act.setEnabled(False)
        self.canvas.draw_idle()


    # ------------------------------------------------------------------ #

    def _on_analysis_change(self, text):
        if text == "radius 1 average":
            self.active_raw = self.vectors_avg_raw
            self.active_norm = self.vectors_avg
        else:  # "basic"
            self.active_raw = self.vectors_raw
            self.active_norm = self.vectors
        # update slider maximum if raw amplitude range changed
        old_max = self.global_amp_max
        self.global_amp_max = float((self.active_raw.max(axis=2) -
                                     self.active_raw.min(axis=2)).max())
        # if self.global_amp_max != old_max:
        #     self.amp_slider.valmax = self.global_amp_max
        #     self.amp_slider.set_val((0.0, self.global_amp_max))
        #     self._style_slider(self.amp_slider,
        #                        label_left="0",
        #                        label_right=str(int(self.global_amp_max)))
        # redraw everything
        self._update_image()
        if self.last_x is not None:
            self._on_click(type("ev", (), {"inaxes": self.ax_image,
                                           "xdata": self.last_x,
                                           "ydata": self.last_y,
                                           "button": 1}))


    # ------------------------------------------------------------------ #
    def _on_amp_change(self, _):
        self._update_image(); self._update_dash_labels()

    def _on_idx_change(self, _):
        low_idx, high_idx = map(int, self.idx_slider.val)
        self.idx_vline_low.set_xdata([low_idx, low_idx])
        self.idx_vline_high.set_xdata([high_idx, high_idx])
        self._update_image(); self._update_dash_labels(); self.canvas.draw_idle()

    # ------------------------------------------------------------------ #
    def _update_image(self):
        if self.vectors is None: return
        low_idx, high_idx = map(int, self.idx_slider.val)

        # Use unnormalized data for image amplitude map
        amp = (self.active_raw[:, :, low_idx - 1:high_idx].max(axis=2) -
               self.active_raw[:, :, low_idx - 1:high_idx].min(axis=2))

        amp_low_frac, amp_high_frac = self.amp_slider.val  # 0–1 on the slider
        amp_low = amp_low_frac * self.global_amp_max  # convert to raw units
        amp_high = amp_high_frac * self.global_amp_max
        span = max(amp_high - amp_low, 1e-6)

        self.current_gray = (np.clip((amp - amp_low) / span, 0, 1) * 255).astype(np.uint8)

        if self.img_handle is None:
            self.img_handle = self.ax_image.imshow(
                self.current_gray, cmap='gray', origin='upper',
                vmin=0, vmax=255, interpolation='nearest')
        else:
            self.img_handle.set_data(self.current_gray)

        self.canvas.draw_idle()

    # ------------------------------------------------------------------ #
    def _update_dash_labels(self):
        l,h = map(int, self.idx_slider.val); self.idx_range_lbl.setText(f"Idx {l}‑{h}")
        al,ah = self.amp_slider.val;
        # self.amp_range_lbl.setText(f"Amp {int(al)}‑{int(ah)}")

        self.amp_range_lbl.setText(f"Amp {al:.2f}‑{ah:.2f}")
    # ------------------------------------------------------------------ #
    def _on_hover(self, event):
        if getattr(self, "ax_image", None) is None or event.inaxes != self.ax_image: return
        x = int(round(event.xdata)) if event.xdata is not None else None
        y = int(round(event.ydata)) if event.ydata is not None else None
        if x is not None and 0 <= x < 245 and 0 <= y < 74:
            self.hover_lbl.setText(f"Hover: (x={x}, y={y})")

    def _on_click(self, event):
        if (getattr(self, "ax_image", None) is None or
                event.inaxes != self.ax_image or event.button != 1): return
        x, y = int(round(event.xdata)), int(round(event.ydata))
        if not (0 <= x < 245 and 0 <= y < 74): return

        # vec = self.vectors[y, x, :]
        vec = self.active_norm[y, x, :]
        self.last_x, self.last_y = x, y; self.selected_lbl.setText(f"Selected: (x={x}, y={y})")

        self.ax_line.clear(); self.ax_line.set_xlabel("Sample index"); self.ax_line.set_ylabel("Amplitude (Normalized)")
        self.ax_line.plot(np.arange(1, 626), vec, lw=1)
        self.ax_line.set_ylim(self.global_min, self.global_max)
        self.ax_line.set_title(f"Measurements for (x={x}, y={y})")

        l,h = map(int, self.idx_slider.val)
        self.idx_vline_low  = self.ax_line.axvline(l, color='red', lw=0.8)
        self.idx_vline_high = self.ax_line.axvline(h, color='red', lw=0.8)
        self.canvas.draw_idle(); self.export_act.setEnabled(True)

    # ------------------------------------------------------------------ #
    def export_image(self):
        if self.current_gray is None:
            QMessageBox.information(self, "Export", "No image to export."); return
        l,h = map(int, self.idx_slider.val); al,ah = self.amp_slider.val
        base = os.path.splitext(os.path.basename(self.current_filename))[0]
        default = f"{base}_x{self.last_x}_y{self.last_y}_idx{l}-{h}_amp{int(al)}-{int(ah)}.png"
        path, _ = QFileDialog.getSaveFileName(self, "Save PNG", default, "PNG Image (*.png)")
        if not path: return
        mpimg.imsave(path, np.kron(self.current_gray, np.ones((4,4),dtype=np.uint8)), cmap='gray')
        self.statusBar().showMessage(f"Saved {path}", 5000)


def main():
    app = QApplication(sys.argv); viewer = ScanViewer(); viewer.show(); sys.exit(app.exec_())


if __name__ == "__main__":
    main()
