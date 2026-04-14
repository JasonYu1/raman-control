from __future__ import annotations
from .spectra import SpectraCollector
from .calibration import CoordTransformer
from .daq import DaqController
from pyAndorSDK2 import atmcd, atmcd_codes, atmcd_errors
import time
import numpy as np
from pyAndorSpectrograph.spectrograph import ATSpectrograph


class AndorSpectraCollector(SpectraCollector):
    _instance = None

    @classmethod
    def instance(
        cls,
        laser_controller: DaqController = None,
        coord_transformer: CoordTransformer = None,
    ) -> AndorSpectraCollector:
        if cls._instance is None:
            cls._instance = cls(laser_controller, coord_transformer)
        return cls._instance

    def __init__(self, laser_controller: DaqController = None, coord_transformer: CoordTransformer = None,):
        super().__init__(laser_controller, coord_transformer)
        self._sdk = atmcd()
        self._sdk.Initialize("")
        self._exposure = 1000
        self.set_temp(-70)
        self._spc = ATSpectrograph()
        self._spc.Initialize("")

    def set_temp(self, temp: float, block=False):
        """
        Parameters
        ----------
        temp : int
            Camera temperature in degrees C
        block : bool, default False
            Whether to block execution until the temperature is reached

        """
        ret = self._sdk.SetTemperature(temp)
        print("Function SetTemperature returned {} target temperature {}".format(ret, temp))

        ret = self._sdk.CoolerON()
        print("Function CoolerON returned {}".format(ret))

        if block:
            while ret != atmcd_errors.Error_Codes.DRV_TEMP_STABILIZED:
                time.sleep(1)
                (ret, temperature) = self._sdk.GetTemperature()
                print("Function GetTemperature returned {} current temperature = {} ".format(
                        ret, temperature), end='\r')
            # Catches above the print statement and preserves the below printstatement
            print("")
            print("Temperature stabilized")

    def get_temp(self) -> float:
        (ret, temperature) = self._sdk.GetTemperature()
        return temperature
    def print_temp(self) -> None:
        (ret, temperature) = self._sdk.GetTemperature()
        print("Function GetTemperature returned {} current temperature = {} ".format(
                ret, temperature), end='\r')

    def set_rm_exposure(self, exposure: float):
        # andor takes times in seconds, not milliseconds
        self._sdk.SetExposureTime(exposure/1000)
        self._exposure = exposure

    def collect_spectra_volts(self, volts, exposure: float):

        exposure = exposure /1000
        volts = np.ascontiguousarray(volts)
        self._daq_controller.prepare_for_collection(np.ascontiguousarray(volts.T))
        N = volts.shape[0]
        self._sdk.SetAcquisitionMode(atmcd_codes.Acquisition_Mode.KINETICS)
        ret = self._sdk.SetReadMode(atmcd_codes.Read_Mode.FULL_VERTICAL_BINNING)
        self._sdk.SetBaselineClamp(0)
        self._sdk.SetPreAmpGain(0)
        self._sdk.SetHSSpeed(0, 2)
        self._sdk.SetVSSpeed(0)
        self._sdk.SetExposureTime(exposure)
        self._sdk.SetNumberAccumulations(1)
        self._sdk.SetNumberKinetics(N)
        self._sdk.SetOutputAmplifier(0)
        self._sdk.SetEMGainMode(0)
        # self._sdk.SetEMCCDGain(255)
        self._sdk.PrepareAcquisition()
        self._sdk.StartAcquisition()
        while self._sdk.GetStatus()[1] == atmcd_errors.Error_Codes.DRV_ACQUIRING:
            time.sleep(0.1)
            print(self._sdk.GetAcquisitionProgress(), end="\r")
        # core.setShutterOpen("Fluoshutter", False)
        data_size = N * 2000
        ret, data = self._sdk.GetAcquiredData(data_size)
        data = data.reshape(N, 2000)
        return data


    def collect_spectra_pts(self, volts, exposure: float):

        exposure = exposure /1000
        volts = np.ascontiguousarray(volts)
        self._daq_controller.prepare_for_collection(np.ascontiguousarray(volts.T))
        N = volts.shape[0]
        self._sdk.SetAcquisitionMode(atmcd_codes.Acquisition_Mode.KINETICS)
        ret = self._sdk.SetReadMode(atmcd_codes.Read_Mode.FULL_VERTICAL_BINNING)
        self._sdk.SetBaselineClamp(0)
        self._sdk.SetPreAmpGain(0)
        self._sdk.SetHSSpeed(0, 2)
        self._sdk.SetVSSpeed(0)
        self._sdk.SetExposureTime(exposure)
        self._sdk.SetNumberAccumulations(1)
        self._sdk.SetNumberKinetics(N)
        self._sdk.SetOutputAmplifier(0)
        self._sdk.SetEMGainMode(0)
        # self._sdk.SetEMCCDGain(255)
        self._sdk.PrepareAcquisition()
        self._sdk.StartAcquisition()
        while self._sdk.GetStatus()[1] == atmcd_errors.Error_Codes.DRV_ACQUIRING:
            time.sleep(0.1)
            print(self._sdk.GetAcquisitionProgress(), end="\r")
        # core.setShutterOpen("Fluoshutter", False)
        data_size = N * 2000
        ret, data = self._sdk.GetAcquiredData(data_size)
        data = data.reshape(N, 2000)
        return data

    # sdk.WaitForAcquisition()

    def collect_spectra_pts_batch(self, volts, exposure: float):

        exposure = exposure /1000
        volts = np.ascontiguousarray(volts)
        self._daq_controller.prepare_for_collection(np.ascontiguousarray(volts.T), batch=True, exposure=exposure)
        # N = volts.shape[0]
        N = 1
        self._sdk.SetAcquisitionMode(atmcd_codes.Acquisition_Mode.KINETICS)
        ret = self._sdk.SetReadMode(atmcd_codes.Read_Mode.FULL_VERTICAL_BINNING)
        self._sdk.SetBaselineClamp(0)
        self._sdk.SetPreAmpGain(0)
        self._sdk.SetHSSpeed(0, 2)
        self._sdk.SetVSSpeed(0)
        self._sdk.SetExposureTime(exposure)
        self._sdk.SetNumberAccumulations(1)
        self._sdk.SetNumberKinetics(N)
        self._sdk.SetOutputAmplifier(0)
        self._sdk.SetEMGainMode(0)
        # self._sdk.SetEMCCDGain(255)
        self._sdk.PrepareAcquisition()
        self._sdk.StartAcquisition()
        while self._sdk.GetStatus()[1] == atmcd_errors.Error_Codes.DRV_ACQUIRING:
            time.sleep(0.1)
            print(self._sdk.GetAcquisitionProgress(), end="\r")
        # core.setShutterOpen("Fluoshutter", False)
        data_size = N * 2000
        ret, data = self._sdk.GetAcquiredData(data_size)
        data = data.reshape(N, 2000)
        return data


    def close(self):
        self._daq_controller.close()
        self._sdk.ShutDown()
        self._spc.Close()
