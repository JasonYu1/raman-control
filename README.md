# raman-control

`raman-control` provides the hardware-control layer for a custom Raman microscope. It coordinates the Raman detector, spectrograph, National Instruments DAQ, galvo scanning, laser shutter, filter actuator, and coordinate calibration used during spectral acquisition.

The package is designed to isolate hardware-specific code from the rest of the acquisition stack. Camera and spectrograph integrations live in collector modules in this repository, while DAQ, galvo, shutter, filter, and other device control is implemented in `raman_control.daq`. Experiment sequencing and the user interface are handled by the companion packages:

- [`raman-mda-engine`](https://github.com/JasonYu1/raman-mda-engine) - Raman acquisition and MDA orchestration
- [`napari-raman-widget`](https://github.com/JasonYu1/napari-raman-widget) - napari-based user interface for operating the microscope

## Hardware-specific collectors

Different Raman systems use different camera SDKs. Instead of embedding those SDK calls in the MDA engine or napari widget, each detector is represented by a collector class in `raman-control`.

Two integrations are included as examples:

- `raman_control.andor.AndorSpectraCollector` uses the Andor camera and spectrograph SDKs.
- `raman_control.princeton.SpectraCollector` is a Princeton Instruments/LightField integration template. The LightField setup and acquisition calls are currently commented out and must be enabled and configured for the local system before use.

Select the collector that matches the installed hardware, then use that class wherever the downstream packages create or receive a collector. Changing detector hardware should require changes to the collector integration, not a rewrite of the experiment or UI logic.

## Rig-specific DAQ configuration

The included `raman_control.daq` module reflects the wiring and hardware configuration of the original microscope. Users may need to modify or replace it to match their own system, including:

- DAQ device names and analog or digital channel assignments
- galvo mirror voltage ranges, scaling, polarity, and scan timing
- laser shutter control and trigger logic
- filter actuator control
- camera trigger synchronization
- any additional peripherals used by the microscope

A custom DAQ controller should preserve the methods and context managers used by the selected collector, such as `instance()`, `prepare_for_collection(...)`, galvo stop control, shutter control, filter insertion and removal, and `close()`. The exact requirements depend on which collector methods and downstream acquisition features are used.

Treat all example channel names, voltage limits, and timing parameters as instrument-specific defaults. Verify the wiring and safe operating range of every connected device before enabling laser output or moving the galvo mirrors.

### Andor example

```python
from raman_control.andor import AndorSpectraCollector

# Use a singleton so the camera, spectrograph, and DAQ are initialized only once.
collector = AndorSpectraCollector.instance()

points = ...  # array with shape (N, 2), in normalized image coordinates
spectra = collector.collect_spectra_relative(points, exposure=500)  # milliseconds
```

For points already expressed as galvo voltages, use `collect_spectra_volts(points, exposure=...)`.

## Supporting another detector

To add a camera or spectrograph that is not already supported:

1. Create a new collector module in `raman_control` (for example, `raman_control/my_camera.py`).
2. Reuse or subclass the shared collector behavior where practical, including the DAQ controller and coordinate transformer. Supply a compatible custom DAQ controller if the microscope uses different galvo wiring or peripheral hardware.
3. Implement the vendor-specific initialization, exposure control, acquisition, data conversion, and cleanup methods.
4. Preserve the interface expected by the downstream packages. At minimum, the collector should provide:

   - `instance(...)` for one-time hardware initialization
   - `collect_spectra_relative(points, exposure)` for normalized `(N, 2)` coordinates
   - `collect_spectra_volts(points, exposure)` for voltage-space `(N, 2)` coordinates
   - `coord_transformer` and `daq` accessors
   - `close()` for releasing hardware resources

5. Update the collector import or dependency injection point in `raman-mda-engine` or `napari-raman-widget` to use the new class.

The returned spectral array should contain one row per requested point. The number of columns is detector-dependent.

## Installation

This project controls laboratory hardware and is intended to be installed from source in the same environment as the companion packages:

```bash
git clone https://github.com/JasonYu1/raman-control.git
cd raman-control
pip install -e .
```

Install the SDK and Python dependencies required by the selected hardware separately:

- **Andor:** install the Andor camera and spectrograph SDKs and their Python packages.
- **Princeton Instruments:** install LightField and its automation libraries. The current integration uses `pythonnet` to access the .NET API.
- **DAQ:** install the National Instruments drivers required by `nidaqmx`, then configure `raman_control.daq` for the device names, channels, wiring, voltage limits, triggers, and peripherals used by the local microscope.

Hardware vendor SDKs are not bundled with this repository. Because the Princeton/LightField API depends on .NET and vendor software, that integration is intended for a compatible Windows acquisition computer.

## Development status

This project is research software for a custom microscope. Hardware settings, calibration files, detector dimensions, voltage limits, and SDK initialization may need to be adapted and validated for each instrument before acquisition. Always confirm safe galvo voltage limits and shutter behavior on the target system.

## License

`raman-control` is distributed under the BSD 3-Clause License.
