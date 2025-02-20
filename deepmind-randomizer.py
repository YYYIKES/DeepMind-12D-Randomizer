# Behringer Deepmind 12 Randomizer
# Version 1.1.0 (GUI)

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import random
import mido
import rtmidi
import pickle
from tkinter import font


# --- Error Handling ---


# Custom error dialog window
class CustomError(tk.Toplevel):
    def __init__(self, parent, title, message):

        super().__init__(parent)
        self.title(title)
        self.geometry("400x100")
        self.resizable(False, False)

        self.transient(parent)  # Make the dialog stay on top of the parent
        self.grab_set()  # Make the dialog modal (prevent interaction with the parent)

        ttk.Label(self, text=message, wraplength=350).pack(pady=10, padx=10)
        ttk.Button(self, text="OK", command=self.destroy).pack(pady=5)

        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")


# --- Main Application ---


# The main application window
class DeepMindRandomizer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("DeepMind Randomizer")
        self.geometry("1300x720")  # Set a specific window size

        # Load parameter metadata (ranges, groups, names)
        self.load_parameter_data()

        # --- Initialize GUI variables ---

        # The name of the DeepMind MIDI device (default: "Deepmind12D")
        self.device_name = tk.StringVar(value="Deepmind12D")

        self.skip_params = {param: tk.BooleanVar(value=False) for param in range(223)}
        self.randomize_buttons = []  # Store references to all randomize buttons

        # Set default skipped parameters (these are parameters commonly *not* randomized)
        for param in [36, 37, 40, 43, 80, 82]:
            self.skip_params[param].set(True)

        # Initialize parameter ranges (min/max values).  Defaults: min=0, max=parameter's maximum value.
        self.param_ranges = {}
        for param in range(223):
            max_val = self.ranges[
                param
            ]  # Get the maximum possible value from the loaded data
            self.param_ranges[param] = {
                "min": tk.IntVar(value=0),
                "max": tk.IntVar(value=max_val),
            }

        # Get available MIDI ports
        self.available_ports = self.get_midi_ports()

        # Create the tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Create the main tabs
        self.create_main_tab()  # "Randomize" tab
        self.create_settings_tab()  # "Settings" tab

        # Load default settings (if they exist)
        self.load_default_settings()

    # Gets a list of available MIDI output port names
    # Returns List[str]: A list of MIDI output port names
    def get_midi_ports(self) -> List[str]:
        return mido.get_output_names()

    # Sends an NRPN (Non-Registered Parameter Number) MIDI message
    def send_nrpn_message(self, port_name: str, parameter: int, value: int):
        """
        Args:
            port_name (str): The name of the MIDI output port.
            parameter (int): The NRPN parameter number (0-222).
            value (int): The value to set for the parameter.
        Raises:
            CustomError: If there's an error sending the MIDI message
        """
        try:
            with mido.open_output(port_name) as outport:
                # Send the NRPN message as a sequence of Control Change messages
                # NRPN MSB (CC 99)
                outport.send(
                    mido.Message(
                        "control_change", control=99, value=(parameter >> 7) & 0x7F
                    )
                )
                # NRPN LSB (CC 98)
                outport.send(
                    mido.Message("control_change", control=98, value=parameter & 0x7F)
                )
                # Data Entry MSB (CC 6)
                outport.send(
                    mido.Message("control_change", control=6, value=(value >> 7) & 0x7F)
                )
                # Data Entry LSB (CC 38)
                outport.send(
                    mido.Message("control_change", control=38, value=value & 0x7F)
                )
        except Exception as e:
            CustomError(self, "MIDI Error", f"Failed to send MIDI message: {str(e)}")

    def disable_all_randomize_buttons(self):
        # Disables all 'Randomize' buttons in the UI
        for button in self.randomize_buttons:
            button.configure(state="disabled")

    def enable_all_randomize_buttons(self):
        # Enables all 'Randomize' buttons in the UI
        for button in self.randomize_buttons:
            button.configure(state="normal")

    # Randomizes parameters via NRPN messages.
    def randomize(self, params: Optional[List[int]] = None):
        """
        Args:
            params (Optional[List[int]]):  A list of parameter numbers to randomize.
                If None (default), randomizes all parameters that are *not* skipped.
                (i.e., all parameters where `self.skip_params[param].get()` is True).
        Raises:
            CustomError: If the MIDI device is not found or if randomization fails.
        """

        # Disable buttons to prevent MIDI message overloading
        self.disable_all_randomize_buttons()

        try:
            # Determine which parameters to randomize
            if params is None:
                # Randomize all checked parameters
                params = [p for p in range(223) if self.skip_params[p].get()]
            else:
                # Ensure that only parameters that are *allowed* to be randomized are included
                params = [p for p in params if self.skip_params[p].get()]

            # Find the MIDI port by the device name
            port_name = None
            device_name = self.device_name.get()
            for available_port in self.available_ports:
                if device_name.lower() in available_port.lower():
                    port_name = available_port
                    break

            # Raise error if midi port not found
            if not port_name:
                CustomError(self, "Error", f"MIDI device '{device_name}' not found")
                self.enable_all_randomize_buttons()  # Re-enable buttons before returning
                return

            # Randomize each parameter
            for param in params:
                # Get min/max values from the UI, ensuring they are valid
                min_val = self.param_ranges[param]["min"].get()
                max_val = self.param_ranges[param]["max"].get()

                # Validate min and max: swap if min > max, clamp to allowed ranges
                if min_val > max_val:
                    min_val, max_val = max_val, min_val
                if min_val < 0:
                    min_val = 0
                if max_val > self.ranges[param]:
                    max_val = self.ranges[param]

                # Generate a random value within the validated range
                new_value = random.randint(min_val, max_val)

                # Send the NRPN message
                self.send_nrpn_message(port_name, param, new_value)

                # Update the UI to prevent freezing (important for long operations)
                self.update_idletasks()

        except Exception as e:
            CustomError(self, "Error", f"Failed to execute randomization: {str(e)}")
        finally:
            # Always re-enable buttons, even if an error occurred
            self.enable_all_randomize_buttons()

    # Loads parameter data: ranges, group assignments, and names
    def load_parameter_data(self):
        # Parameter ranges: The maximum value for each parameter
        self.ranges = [
            255,  # 0:   LFO1 Rate
            255,  # 1:   LFO1 Delay
            6,  # 2:   LFO1 Shape
            1,  # 3:   LFO1 Key Sync
            1,  # 4:   LFO1 Arp Sync
            1,  # 5:   LFO1 Mono Mode
            255,  # 6:   LFO1 Slew
            255,  # 7:   LFO2 Rate
            255,  # 8:   LFO2 Delay
            6,  # 9:   LFO2 Shape
            1,  # 10:  LFO2 Key Sync
            1,  # 11:  LFO2 Arp Sync
            255,  # 12:  LFO2 Mono Mode
            255,  # 13:  LFO2 Slew
            2,  # 14:  OSC1 Range
            2,  # 15:  OSC2 Range
            5,  # 16:  OSC1 PWM Src
            5,  # 17:  OSC2 TM Src
            1,  # 18:  OSC1 Pulse
            1,  # 19:  OSC1 Saw
            1,  # 20:  OSC Sync
            255,  # 21:  OSC1 PM Depth
            6,  # 22:  OSC1 PM Select
            255,  # 23:  OSC1 ATouch>PM Depth
            255,  # 24:  OSC1 MW>PM Depth
            255,  # 25:  OSC1 PWM Depth
            255,  # 26:  OSC2 Level
            255,  # 27:  OSC2 Pitch
            255,  # 28:  OSC2 TM Depth
            255,  # 29:  OSC2 PM Depth
            255,  # 30:  OSC2 ATouch>PM Depth
            255,  # 31:  OSC2 MW>PM Depth
            6,  # 32:  OSC2 PM Select
            255,  # 33:  Noise Level
            255,  # 34:  Porta Time
            13,  # 35:  Porta Mode
            24,  # 36:  PB+ Depth
            24,  # 37:  PB- Depth
            1,  # 38:  OSC1 PM Mode
            255,  # 39:  VCF Freq
            255,  # 40:  VCF HPF
            255,  # 41:  VCF Reso
            255,  # 42:  VCF Env Depth
            255,  # 43:  VCF Env Velo Sens
            255,  # 44:  VCF PB>Freq Depth
            255,  # 45:  VCF LFO Depth
            1,  # 46:  VCF LFO Select
            255,  # 47:  VCF ATouch>LFO Depth
            255,  # 48:  VCF MW>LFO Depth
            255,  # 49:  VCF Keytrack
            1,  # 50:  VCF Env Polarity
            1,  # 51:  VCF 2 Pole
            1,  # 52:  VCF Boost
            255,  # 53:  VCA Env Atk
            255,  # 54:  VCA Env Dec
            255,  # 55:  VCA Env Sust
            255,  # 56:  VCA Env Rel
            4,  # 57:  VCA Env Trig Mode
            255,  # 58:  VCA Env Atk Curve
            255,  # 59:  VCA Env Dec Curve
            255,  # 60:  VCA Env Sust Curve
            255,  # 61:  VCA Env Rrel Curve
            255,  # 62:  VCF Env Atk
            255,  # 63:  VCF Env Dec
            255,  # 64:  VCF Env Sust
            255,  # 65:  VCF Env Rel
            4,  # 66:  VCF Env Trig Mode
            255,  # 67:  VCF Env Atk Curve
            255,  # 68:  VCF Env Dec Curve
            255,  # 69:  VCF Env Sust Curve
            255,  # 70:  VCF Env Rel Curve
            255,  # 71:  Mod Env Atk
            255,  # 72:  Mod Env Dec
            255,  # 73:  Mod Env Sust
            255,  # 74:  Mod Env Rel
            4,  # 75:  Mod Env Trig Mode
            255,  # 76:  Mod Env Atk Curve
            255,  # 77:  Mod Env Dec Curve
            255,  # 78:  Mod Env Sust Curve
            255,  # 79:  Mod Env Rel Curve
            255,  # 80:  VCA Level
            255,  # 81:  VCA Env Depth
            255,  # 82:  VCA Env Velo Sens
            255,  # 83:  VCA Pan Spread
            2,  # 84:  Voice Priority Mode
            12,  # 85:  Polyphony Mode
            3,  # 86:  Env Trigger Mode
            255,  # 87:  Unison Detune
            255,  # 88:  Voice Drift
            255,  # 89:  Parameter Drift
            255,  # 90:  Drift Rate
            255,  # 91:  OSC Porta Balance
            1,  # 92:  OSC Key Reset
            22,  # 93:  Mod1 Src
            129,  # 94:  Mod1 Dest
            255,  # 95:  Mod1 Depth
            22,  # 96:  Mod2 Src
            129,  # 97:  Mod2 Dest
            255,  # 98:  Mod2 Depth
            22,  # 99:  Mod3 Src
            129,  # 100: Mod3 Dest
            255,  # 101: Mod3 Depth
            22,  # 102: Mod4 Src
            129,  # 103: Mod4 Dest
            255,  # 104: Mod4 Depth
            22,  # 105: Mod5 Src
            129,  # 106: Mod5 Dest
            255,  # 107: Mod5 Depth
            22,  # 108: Mod6 Src
            129,  # 109: Mod6 Dest
            255,  # 110: Mod6 Depth
            22,  # 111: Mod7 Src
            129,  # 112: Mod7 Dest
            255,  # 113: Mod7 Depth
            22,  # 114: Mod8 Src
            129,  # 115: Mod8 Dest
            255,  # 116: Mod8 Depth
            1,  # 117: Ctrl Seq Enable
            15,  # 118: Ctrl Seq Clock
            31,  # 119: Sequence Length
            25,  # 120: Sequencer Swing
            2,  # 121: Key Sync & Loop
            255,  # 122: Slew
            255,  # 123: Seq Step 1
            255,  # 124: Seq Step 2
            255,  # 125: Seq Step 3
            255,  # 126: Seq Step 4
            255,  # 127: Seq Step 5
            255,  # 128: Seq Step 6
            255,  # 129: Seq Step 7
            255,  # 130: Seq Step 8
            255,  # 131: Seq Step 9
            255,  # 132: Seq Step 10
            255,  # 133: Seq Step 11
            255,  # 134: Seq Step 12
            255,  # 135: Seq Step 13
            255,  # 136: Seq Step 14
            255,  # 137: Seq Step 15
            255,  # 138: Seq Step 16
            255,  # 139: Seq Step 17
            255,  # 140: Seq Step 18
            255,  # 141: Seq Step 19
            255,  # 142: Seq Step 20
            255,  # 143: Seq Step 21
            255,  # 144: Seq Step 22
            255,  # 145: Seq Step 23
            255,  # 146: Seq Step 24
            255,  # 147: Seq Step 25
            255,  # 148: Seq Step 26
            255,  # 149: Seq Step 27
            255,  # 150: Seq Step 28
            255,  # 151: Seq Step 29
            255,  # 152: Seq Step 30
            255,  # 153: Seq Step 31
            255,  # 154: Seq Step 32
            1,  # 155: Arp On/Off
            10,  # 156: Arp Mode
            255,  # 157: Arp Rate
            12,  # 158: Arp Clock
            1,  # 159: Arp Key Sync
            255,  # 160: Arp Gate
            1,  # 161: Arp Hold
            64,  # 162: Arp Pattern
            25,  # 163: Arp Swing
            5,  # 164: Arp Octaves
            9,  # 165: FX Routing
            33,  # 166: FX1 Type
            255,  # 167: FX1 Param 1
            255,  # 168: FX1 Param 2
            255,  # 169: FX1 Param 3
            255,  # 170: FX1 Param 4
            255,  # 171: FX1 Param 5
            255,  # 172: FX1 Param 6
            255,  # 173: FX1 Param 7
            255,  # 174: FX1 Param 8
            255,  # 175: FX1 Param 9
            255,  # 176: FX1 Param 10
            255,  # 177: FX1 Param 11
            255,  # 178: FX1 Param 12
            33,  # 179: FX2 Type
            255,  # 180: FX2 Param 1
            255,  # 181: FX2 Param 2
            255,  # 182: FX2 Param 3
            255,  # 183: FX2 Param 4
            255,  # 184: FX2 Param 5
            255,  # 185: FX2 Param 6
            255,  # 186: FX2 Param 7
            255,  # 187: FX2 Param 8
            255,  # 188: FX2 Param 9
            255,  # 189: FX2 Param 10
            255,  # 190: FX2 Param 11
            255,  # 191: FX2 Param 12
            33,  # 192: FX3 Type
            255,  # 193: FX3 Param 1
            255,  # 194: FX3 Param 2
            255,  # 195: FX3 Param 3
            255,  # 196: FX3 Param 4
            255,  # 197: FX3 Param 5
            255,  # 198: FX3 Param 6
            255,  # 199: FX3 Param 7
            255,  # 200: FX3 Param 8
            255,  # 201: FX3 Param 9
            255,  # 202: FX3 Param 10
            255,  # 203: FX3 Param 11
            255,  # 204: FX3 Param 12
            33,  # 205: FX4 Type
            255,  # 206: FX4 Param 1
            255,  # 207: FX4 Param 2
            255,  # 208: FX4 Param 3
            255,  # 209: FX4 Param 4
            255,  # 210: FX4 Param 5
            255,  # 211: FX4 Param 6
            255,  # 212: FX4 Param 7
            255,  # 213: FX4 Param 8
            255,  # 214: FX4 Param 9
            255,  # 215: FX4 Param 10
            255,  # 216: FX4 Param 11
            255,  # 217: FX4 Param 12
            150,  # 218: FX1 Gain
            0,  # 219: FX2 Gain
            0,  # 220: FX3 Gain
            150,  # 221: FX4 Gain
            2,  # 222: FX Mode
        ]

        # Parameter groups: Organizes parameters into logical sections
        self.param_groups = {
            "OSC": [
                14,  # OSC1 Range
                15,  # OSC2 Range
                16,  # OSC1 PWM Src
                17,  # OSC2 TM Src
                18,  # OSC1 Pulse
                19,  # OSC1 Saw
                20,  # OSC Sync
                21,  # OSC1 PM Depth
                22,  # OSC1 PM Select
                23,  # OSC1 ATouch>PM Depth
                24,  # OSC1 MW>PM Depth
                25,  # OSC1 PWM Depth
                26,  # OSC2 Level
                27,  # OSC2 Pitch
                28,  # OSC2 TM Depth
                29,  # OSC2 PM Depth
                30,  # OSC2 ATouch>PM Depth
                31,  # OSC2 MW>PM Depth
                32,  # OSC2 PM Select
                33,  # Noise Level
                38,  # OSC1 PM Mode
                91,  # OSC Porta Balance
                92,  # OSC Key Reset
            ],
            "VCA": [
                53,  # VCA Env Atk
                54,  # VCA Env Dec
                55,  # VCA Env Sust
                56,  # VCA Env Rel
                57,  # VCA Env Trig Mode
                58,  # VCA Env Atk Curve
                59,  # VCA Env Dec Curve
                60,  # VCA Env Sust Curve
                61,  # VCA Env Rrel Curve
                80,  # VCA Level
                81,  # VCA Env Depth
                82,  # VCA Env Velo Sens
                83,  # VCA Pan Spread
            ],
            "VCF": [
                39,  # VCF Freq
                40,  # VCF HPF
                41,  # VCF Reso
                42,  # VCF Env Depth
                43,  # VCF Env Velo Sens
                44,  # VCF PB>Freq Depth
                45,  # VCF LFO Depth
                46,  # VCF LFO Select
                47,  # VCF ATouch>LFO Depth
                48,  # VCF MW>LFO Depth
                49,  # VCF Keytrack
                50,  # VCF Env Polarity
                51,  # VCF 2 Pole
                52,  # VCF Boost
            ],
            "ENV": [
                53,  # VCA Env Atk
                54,  # VCA Env Dec
                55,  # VCA Env Sust
                56,  # VCA Env Rel
                57,  # VCA Env Trig Mode
                58,  # VCA Env Atk Curve
                59,  # VCA Env Dec Curve
                60,  # VCA Env Sust Curve
                61,  # VCA Env Rrel Curve
                62,  # VCF Env Atk
                63,  # VCF Env Dec
                64,  # VCF Env Sust
                65,  # VCF Env Rel
                66,  # VCF Env Trig Mode
                67,  # VCF Env Atk Curve
                68,  # VCF Env Dec Curve
                69,  # VCF Env Sust Curve
                70,  # VCF Env Rel Curve
                71,  # Mod Env Atk
                72,  # Mod Env Dec
                73,  # Mod Env Sust
                74,  # Mod Env Rel
                75,  # Mod Env Trig Mode
                76,  # Mod Env Atk Curve
                77,  # Mod Env Dec Curve
                78,  # Mod Env Sust Curve
                79,  # Mod Env Rel Curve
            ],
            "ARP/SEQ": [
                117,  # Ctrl Seq Enable
                118,  # Ctrl Seq Clock
                119,  # Sequence Length
                120,  # Sequencer Swing
                121,  # Key Sync & Loop
                122,  # Slew
                123,  # Seq Step 1
                124,  # Seq Step 2
                125,  # Seq Step 3
                126,  # Seq Step 4
                127,  # Seq Step 5
                128,  # Seq Step 6
                129,  # Seq Step 7
                130,  # Seq Step 8
                131,  # Seq Step 9
                132,  # Seq Step 10
                133,  # Seq Step 11
                134,  # Seq Step 12
                135,  # Seq Step 13
                136,  # Seq Step 14
                137,  # Seq Step 15
                138,  # Seq Step 16
                139,  # Seq Step 17
                140,  # Seq Step 18
                141,  # Seq Step 19
                142,  # Seq Step 20
                143,  # Seq Step 21
                144,  # Seq Step 22
                145,  # Seq Step 23
                146,  # Seq Step 24
                147,  # Seq Step 25
                148,  # Seq Step 26
                149,  # Seq Step 27
                150,  # Seq Step 28
                151,  # Seq Step 29
                152,  # Seq Step 30
                153,  # Seq Step 31
                154,  # Seq Step 32
                155,  # Arp On/Off
                156,  # Arp Mode
                157,  # Arp Rate
                158,  # Arp Clock
                159,  # Arp Key Sync
                160,  # Arp Gate
                161,  # Arp Hold
                162,  # Arp Pattern
                163,  # Arp Swing
                164,  # Arp Octaves
            ],
            "LFO": [
                0,  # LFO1 Rate
                1,  # LFO1 Delay
                2,  # LFO1 Shape
                3,  # LFO1 Key Sync
                4,  # LFO1 Arp Sync
                5,  # LFO1 Mono Mode
                6,  # LFO1 Slew
                7,  # LFO2 Rate
                8,  # LFO2 Delay
                9,  # LFO2 Shape
                10,  # LFO2 Key Sync
                11,  # LFO2 Arp Sync
                12,  # LFO2 Mono Mode
                13,  # LFO2 Slew
            ],
            "FX": [
                165,  # FX Routing
                166,  # FX1 Type
                167,  # FX1 Param 1
                168,  # FX1 Param 2
                169,  # FX1 Param 3
                170,  # FX1 Param 4
                171,  # FX1 Param 5
                172,  # FX1 Param 6
                173,  # FX1 Param 7
                174,  # FX1 Param 8
                175,  # FX1 Param 9
                176,  # FX1 Param 10
                177,  # FX1 Param 11
                178,  # FX1 Param 12
                179,  # FX2 Type
                180,  # FX2 Param 1
                181,  # FX2 Param 2
                182,  # FX2 Param 3
                183,  # FX2 Param 4
                184,  # FX2 Param 5
                185,  # FX2 Param 6
                186,  # FX2 Param 7
                187,  # FX2 Param 8
                188,  # FX2 Param 9
                189,  # FX2 Param 10
                190,  # FX2 Param 11
                191,  # FX2 Param 12
                192,  # FX3 Type
                193,  # FX3 Param 1
                194,  # FX3 Param 2
                195,  # FX3 Param 3
                196,  # FX3 Param 4
                197,  # FX3 Param 5
                198,  # FX3 Param 6
                199,  # FX3 Param 7
                200,  # FX3 Param 8
                201,  # FX3 Param 9
                202,  # FX3 Param 10
                203,  # FX3 Param 11
                204,  # FX3 Param 12
                205,  # FX4 Type
                206,  # FX4 Param 1
                207,  # FX4 Param 2
                208,  # FX4 Param 3
                209,  # FX4 Param 4
                210,  # FX4 Param 5
                211,  # FX4 Param 6
                212,  # FX4 Param 7
                213,  # FX4 Param 8
                214,  # FX4 Param 9
                215,  # FX4 Param 10
                216,  # FX4 Param 11
                217,  # FX4 Param 12
                218,  # FX1 Gain
                219,  # FX2 Gain
                220,  # FX3 Gain
                221,  # FX4 Gain
                222,  # FX Mode
            ],
            "MOD": [
                93,  # Mod1 Src
                94,  # Mod1 Dest
                95,  # Mod1 Depth
                96,  # Mod2 Src
                97,  # Mod2 Dest
                98,  # Mod2 Depth
                99,  # Mod3 Src
                100,  # Mod3 Dest
                101,  # Mod3 Depth
                102,  # Mod4 Src
                103,  # Mod4 Dest
                104,  # Mod4 Depth
                105,  # Mod5 Src
                106,  # Mod5 Dest
                107,  # Mod5 Depth
                108,  # Mod6 Src
                109,  # Mod6 Dest
                110,  # Mod6 Depth
                111,  # Mod7 Src
                112,  # Mod7 Dest
                113,  # Mod7 Depth
                114,  # Mod8 Src
                115,  # Mod8 Dest
                116,  # Mod8 Depth
            ],
            "POLY": [
                34,  # Porta Time
                35,  # Porta Mode
                36,  # PB+ Depth
                37,  # PB- Depth
                84,  # Voice Priority Mode
                85,  # Polyphony Mode
                86,  # Env Trigger Mode
                87,  # Unison Detune
                88,  # Voice Drift
                89,  # Parameter Drift
                90,  # Drift Rate
                91,  # OSC Porta Balance
                92,  # OSC Key Reset
            ],
        }

        # Parameter names: Maps parameter numbers to human-readable names
        self.param_names = {
            0: "LFO1 Rate",  # 255
            1: "LFO1 Delay",  # 255
            2: "LFO1 Shape",  # 6
            3: "LFO1 Key Sync",  # 1
            4: "LFO1 Arp Sync",  # 1
            5: "LFO1 Mono Mode",  # 1
            6: "LFO1 Slew",  # 255
            7: "LFO2 Rate",  # 255
            8: "LFO2 Delay",  # 255
            9: "LFO2 Shape",  # 6
            10: "LFO2 Key Sync",  # 1
            11: "LFO2 Arp Sync",  # 1
            12: "LFO2 Mono Mode",  # 255
            13: "LFO2 Slew",  # 255
            14: "OSC1 Range",  # 2
            15: "OSC2 Range",  # 2
            16: "OSC1 PWM Src",  # 5
            17: "OSC2 TM Src",  # 5
            18: "OSC1 Pulse",  # 1
            19: "OSC1 Saw",  # 1
            20: "OSC Sync",  # 1
            21: "OSC1 PM Depth",  # 255
            22: "OSC1 PM Select",  # 6
            23: "OSC1 ATouch>PM Depth",  # 255
            24: "OSC1 MW>PM Depth",  # 255
            25: "OSC1 PWM Depth",  # 255
            26: "OSC2 Level",  # 255
            27: "OSC2 Pitch",  # 255
            28: "OSC2 TM Depth",  # 255
            29: "OSC2 PM Depth",  # 255
            30: "OSC2 ATouch>PM Depth",  # 255
            31: "OSC2 MW>PM Depth",  # 255
            32: "OSC2 PM Select",  # 6
            33: "Noise Level",  # 255
            34: "Porta Time",  # 255
            35: "Porta Mode",  # 13
            36: "PB+ Depth",  # 24
            37: "PB- Depth",  # 24
            38: "OSC1 PM Mode",  # 1
            39: "VCF Freq",  # 255
            40: "VCF HPF",  # 255
            41: "VCF Reso",  # 255
            42: "VCF Env Depth",  # 255
            43: "VCF Env Velo Sens",  # 255
            44: "VCF PB>Freq Depth",  # 255
            45: "VCF LFO Depth",  # 255
            46: "VCF LFO Select",  # 1
            47: "VCF ATouch>LFO Depth",  # 255
            48: "VCF MW>LFO Depth",  # 255
            49: "VCF Keytrack",  # 255
            50: "VCF Env Polarity",  # 1
            51: "VCF 2 Pole",  # 1
            52: "VCF Boost",  # 1
            53: "VCA Env Atk",  # 255
            54: "VCA Env Dec",  # 255
            55: "VCA Env Sust",  # 255
            56: "VCA Env Rel",  # 255
            57: "VCA Env Trig Mode",  # 4
            58: "VCA Env Atk Curve",  # 255
            59: "VCA Env Dec Curve",  # 255
            60: "VCA Env Sust Curve",  # 255
            61: "VCA Env Rrel Curve",  # 255
            62: "VCF Env Atk",  # 255
            63: "VCF Env Dec",  # 255
            64: "VCF Env Sust",  # 255
            65: "VCF Env Rel",  # 255
            66: "VCF Env Trig Mode",  # 4,
            67: "VCF Env Atk Curve",  # 255
            68: "VCF Env Dec Curve",  # 255
            69: "VCF Env Sust Curve",  # 255
            70: "VCF Env Rel Curve",  # 255
            71: "Mod Env Atk",  # 255
            72: "Mod Env Dec",  # 255
            73: "Mod Env Sust",  # 255
            74: "Mod Env Rel",  # 255
            75: "Mod Env Trig Mode",  # 4
            76: "Mod Env Atk Curve",  # 255
            77: "Mod Env Dec Curve",  # 255
            78: "Mod Env Sust Curve",  # 255
            79: "Mod Env Rel Curve",  # 255
            80: "VCA Level",  # 255
            81: "VCA Env Depth",  # 255
            82: "VCA Env Velo Sens",  # 255
            83: "VCA Pan Spread",  # 255
            84: "Voice Priority Mode",  # 2
            85: "Polyphony Mode",  # 12
            86: "Env Trigger Mode",  # 3
            87: "Unison Detune",  # 255
            88: "Voice Drift",  # 255
            89: "Parameter Drift",  # 255
            90: "Drift Rate",  # 255
            91: "OSC Porta Balance",  # 255
            92: "OSC Key Reset",  # 1
            93: "Mod1 Src",  # 22
            94: "Mod1 Dest",  # 129
            95: "Mod1 Depth",  # 255
            96: "Mod2 Src",  # 22
            97: "Mod2 Dest",  # 129
            98: "Mod2 Depth",  # 255
            99: "Mod3 Src",  # 22
            100: "Mod3 Dest",  # 129
            101: "Mod3 Depth",  # 255
            102: "Mod4 Src",  # 22
            103: "Mod4 Dest",  # 129
            104: "Mod4 Depth",  # 255
            105: "Mod5 Src",  # 22
            106: "Mod5 Dest",  # 129
            107: "Mod5 Depth",  # 255
            108: "Mod6 Src",  # 22
            109: "Mod6 Dest",  # 129
            110: "Mod6 Depth",  # 255
            111: "Mod7 Src",  # 22
            112: "Mod7 Dest",  # 129
            113: "Mod7 Depth",  # 255
            114: "Mod8 Src",  # 22
            115: "Mod8 Dest",  # 129
            116: "Mod8 Depth",  # 255
            117: "Ctrl Seq Enable",  # 1
            118: "Ctrl Seq Clock",  # 15
            119: "Sequence Length",  # 31
            120: "Sequencer Swing",  # 25
            121: "Key Sync & Loop",  # 2
            122: "Slew",  # 255
            123: "Seq Step 1",  # 255
            124: "Seq Step 2",  # 255
            125: "Seq Step 3",  # 255
            126: "Seq Step 4",  # 255
            127: "Seq Step 5",  # 255
            128: "Seq Step 6",  # 255
            129: "Seq Step 7",  # 255
            130: "Seq Step 8",  # 255
            131: "Seq Step 9",  # 255
            132: "Seq Step 10",  # 255
            133: "Seq Step 11",  # 255
            134: "Seq Step 12",  # 255
            135: "Seq Step 13",  # 255
            136: "Seq Step 14",  # 255
            137: "Seq Step 15",  # 255
            138: "Seq Step 16",  # 255
            139: "Seq Step 17",  # 255
            140: "Seq Step 18",  # 255
            141: "Seq Step 19",  # 255
            142: "Seq Step 20",  # 255
            143: "Seq Step 21",  # 255
            144: "Seq Step 22",  # 255
            145: "Seq Step 23",  # 255
            146: "Seq Step 24",  # 255
            147: "Seq Step 25",  # 255
            148: "Seq Step 26",  # 255
            149: "Seq Step 27",  # 255
            150: "Seq Step 28",  # 255
            151: "Seq Step 29",  # 255
            152: "Seq Step 30",  # 255
            153: "Seq Step 31",  # 255
            154: "Seq Step 32",  # 255
            155: "Arp On/Off",  # 1
            156: "Arp Mode",  # 10
            157: "Arp Rate",  # 255
            158: "Arp Clock",  # 12
            159: "Arp Key Sync",  # 1
            160: "Arp Gate",  # 255
            161: "Arp Hold",  # 1
            162: "Arp Pattern",  # 64
            163: "Arp Swing",  # 25
            164: "Arp Octaves",  # 5
            165: "FX Routing",  # 9
            166: "FX1 Type",  # 33
            167: "FX1 Param 1",  # 255
            168: "FX1 Param 2",  # 255
            169: "FX1 Param 3",  # 255
            170: "FX1 Param 4",  # 255
            171: "FX1 Param 5",  # 255
            172: "FX1 Param 6",  # 255
            173: "FX1 Param 7",  # 255
            174: "FX1 Param 8",  # 255
            175: "FX1 Param 9",  # 255
            176: "FX1 Param 10",  # 255
            177: "FX1 Param 11",  # 255
            178: "FX1 Param 12",  # 255
            179: "FX2 Type",  # 33
            180: "FX2 Param 1",  # 255
            181: "FX2 Param 2",  # 255
            182: "FX2 Param 3",  # 255
            183: "FX2 Param 4",  # 255
            184: "FX2 Param 5",  # 255
            185: "FX2 Param 6",  # 255
            186: "FX2 Param 7",  # 255
            187: "FX2 Param 8",  # 255
            188: "FX2 Param 9",  # 255
            189: "FX2 Param 10",  # 255
            190: "FX2 Param 11",  # 255
            191: "FX2 Param 12",  # 255
            192: "FX3 Type",  # 33
            193: "FX3 Param 1",  # 255
            194: "FX3 Param 2",  # 255
            195: "FX3 Param 3",  # 255
            196: "FX3 Param 4",  # 255
            197: "FX3 Param 5",  # 255
            198: "FX3 Param 6",  # 255
            199: "FX3 Param 7",  # 255
            200: "FX3 Param 8",  # 255
            201: "FX3 Param 9",  # 255
            202: "FX3 Param 10",  # 255
            203: "FX3 Param 11",  # 255
            204: "FX3 Param 12",  # 255
            205: "FX4 Type",  # 33
            206: "FX4 Param 1",  # 255
            207: "FX4 Param 2",  # 255
            208: "FX4 Param 3",  # 255
            209: "FX4 Param 4",  # 255
            210: "FX4 Param 5",  # 255
            211: "FX4 Param 6",  # 255
            212: "FX4 Param 7",  # 255
            213: "FX4 Param 8",  # 255
            214: "FX4 Param 9",  # 255
            215: "FX4 Param 10",  # 255
            216: "FX4 Param 11",  # 255
            217: "FX4 Param 12",  # 255
            218: "FX1 Gain",  # 150
            219: "FX2 Gain",  # 0
            220: "FX3 Gain",  # 0
            221: "FX4 Gain",  # 150
            222: "FX Mode",  # 2
        }

    # Creates the "Randomize" tab, containing the main randomization controls
    def create_main_tab(self):
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Randomize")

        # --- Top Frame: Global Controls ---

        top_frame = ttk.Frame(main_tab)
        top_frame.pack(fill="x", padx=5, pady=5)

        # First Row: MIDI Device and Randomize Buttons
        controls_frame = ttk.Frame(top_frame)
        controls_frame.pack(fill="x", pady=(0, 5))

        # MIDI Device Input
        ttk.Label(controls_frame, text="MIDI Device:").pack(
            side="left", fill="y", padx=5
        )
        ttk.Entry(controls_frame, textvariable=self.device_name).pack(
            side="left", padx=5
        )

        # Separator
        ttk.Separator(controls_frame, orient="vertical").pack(
            side="left", fill="y", padx=10
        )

        # "Randomize:" Label
        ttk.Label(controls_frame, text="Randomize:").pack(side="left", padx=5)

        # Section Randomization Buttons (packed left-to-right)
        for group_name, params in self.param_groups.items():
            button_text = group_name  # Use group name directly
            group_button = ttk.Button(
                controls_frame,
                text=button_text,
                command=lambda g=params: self.randomize(g),
            )
            group_button.pack(side="left", padx=2)
            self.randomize_buttons.append(
                group_button
            )  # Add to the list for enable/disable

        # Spacer before "EVERYTHING!" button
        ttk.Label(controls_frame, text="  ").pack(side="left")

        # Main "EVERYTHING!" (Randomize All) Button - Bold Style
        main_button_style = ttk.Style()
        main_button_style.configure("Bold.TButton", font=("TkDefaultFont", 10, "bold"))
        main_button = ttk.Button(
            controls_frame,
            text="EVERYTHING!",
            command=lambda: self.randomize(),
            style="Bold.TButton",  # Apply the bold style
        )
        main_button.pack(side="right", padx=5)
        self.randomize_buttons.append(main_button)  # Add to the list for enable/disable

        # --- Scrollable Area for Parameter Checkboxes ---

        canvas = tk.Canvas(main_tab, highlightthickness=0)  # No border
        scrollbar = ttk.Scrollbar(main_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Basic scroll configuration
        canvas.configure(yscrollcommand=scrollbar.set)
        window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Update scrollregion when frame changes
        def _configure_frame(event):
            size = (
                scrollable_frame.winfo_reqwidth(),
                scrollable_frame.winfo_reqheight(),
            )
            canvas.configure(scrollregion=f"0 0 {size[0]} {size[1]}")
            canvas.itemconfigure(window, width=canvas.winfo_width())  # Adjust width

        scrollable_frame.bind("<Configure>", _configure_frame)

        # Dynamic width adjustment for the canvas
        def _configure_canvas(event):
            if scrollable_frame.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(window, width=event.width)

        canvas.bind("<Configure>", _configure_canvas)

        # Pack scrollbar and canvas (expand and fill)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # --- Create Parameter Group Sections (Checkboxes) ---

        for group_name, params in self.param_groups.items():
            group_frame = ttk.LabelFrame(scrollable_frame, text=group_name)
            group_frame.pack(fill="x", padx=5, pady=5)

            # Frame for checkboxes within each group
            checkbox_frame = ttk.Frame(group_frame)
            checkbox_frame.pack(fill="x", padx=5, pady=5)

            # "Select All" and "Deselect All" buttons for each group
            group_buttons_frame = ttk.Frame(checkbox_frame)
            group_buttons_frame.grid(
                row=0, column=0, columnspan=4, sticky="w", pady=(0, 5)
            )  # Use grid
            ttk.Button(
                group_buttons_frame,
                text="Select All",
                command=lambda p=params: self.select_group_params(p, True),
            ).pack(side="left", padx=2)
            ttk.Button(
                group_buttons_frame,
                text="Deselect All",
                command=lambda p=params: self.select_group_params(p, False),
            ).pack(side="left", padx=2)

            # Grid layout for checkboxes (4 columns)
            num_cols = 4
            num_rows = (len(params) + num_cols - 1) // num_cols

            # Configure grid columns for equal width
            for i in range(num_cols):
                checkbox_frame.columnconfigure(i, weight=1, uniform="col")

            # Create checkboxes in the grid
            for i, param in enumerate(params):
                row = (i // num_cols) + 1  # Start from row 1 (leave space for buttons)
                col = i % num_cols

                # Initialize checkbox: True (randomize) unless in the default skip list
                should_skip = param in [36, 37, 40, 43, 80, 82, 219, 220]
                self.skip_params[param].set(not should_skip)

                cb = ttk.Checkbutton(
                    checkbox_frame,
                    text=f"{param}: {self.param_names.get(param, f'Param {param}')}",
                    variable=self.skip_params[param],
                )
                cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)

    # Selects or deselects all parameters within a specified group
    def select_group_params(self, params: List[int], select: bool):
        """
        Args:
            params (List[int]): The list of parameter numbers in the group.
            select (bool):  True to select (check) all, False to deselect (uncheck).
        """
        for param in params:
            self.skip_params[param].set(select)

    # Creates the "Settings" tab
    def create_settings_tab(self):
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="Settings")

        # Main container frame
        container = ttk.Frame(settings_tab)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # Buttons for saving and clearing default settings
        button_frame = ttk.Frame(container)
        button_frame.pack(fill="x", pady=(0, 5))

        save_button = ttk.Button(
            button_frame,
            text="Save As Default Settings",
            command=self.save_default_settings,
        )
        save_button.pack(side="left", padx=5)

        clear_button = ttk.Button(
            button_frame,
            text="Clear Default Settings",
            command=self.clear_default_settings,
        )
        clear_button.pack(side="left", padx=5)

        # Scrollable frame for parameter range controls
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Basic scroll configuration
        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Configure canvas background and create window
        canvas.configure(bg=self.cget("bg"))  # Match window background
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # --- Create Three Columns for Parameter Groups ---

        columns = [ttk.Frame(scrollable_frame) for _ in range(3)]
        for col in columns:
            col.pack(side="left", fill="both", expand=True, padx=5)

        # Distribute parameter groups evenly across the three columns
        groups = list(self.param_groups.items())
        items_per_column = (len(groups) + 2) // 3

        for i, (group_name, params) in enumerate(groups):
            # Determine which column to use
            column_index = i // items_per_column
            if column_index >= 3:  # Ensure we don't go beyond the available columns
                column_index = 2

            group_frame = ttk.LabelFrame(columns[column_index], text=group_name)
            group_frame.pack(fill="x", pady=5)

            # Headers for the table (Parameter, Min, Max)
            ttk.Label(group_frame, text="Parameter").grid(
                row=0, column=0, padx=5, sticky="w"
            )
            ttk.Label(group_frame, text="Min").grid(row=0, column=1, padx=5)
            ttk.Label(group_frame, text="Max").grid(row=0, column=2, padx=5)

            # Configure grid column weights for layout.
            group_frame.columnconfigure(0, weight=1)  # Parameter name column expands
            group_frame.columnconfigure(1, minsize=50)  # Min column - fixed width
            group_frame.columnconfigure(2, minsize=50)  # Max column - fixed width

            # Create parameter range controls (label and two entry fields)
            for j, param in enumerate(params):
                ttk.Label(
                    group_frame,
                    text=f"{param}: {self.param_names.get(param, f'Param {param}')}",
                ).grid(row=j + 1, column=0, sticky="w", padx=5, pady=2)

                ttk.Entry(
                    group_frame, textvariable=self.param_ranges[param]["min"], width=5
                ).grid(row=j + 1, column=1, padx=5, pady=2)

                ttk.Entry(
                    group_frame, textvariable=self.param_ranges[param]["max"], width=5
                ).grid(row=j + 1, column=2, padx=5, pady=2)

    # Saves the current application settings as the default
    def save_default_settings(self):
        """
        Saves values for:
            - MIDI device name.
            - Skipped parameters (checkbox states).
            - Parameter ranges (min/max values).

        Settings are saved to a file named ".deepmind_defaults" (hidden file)
        """
        settings = {
            "device_name": self.device_name.get(),
            "skip_params": {
                param: var.get() for param, var in self.skip_params.items()
            },
            "param_ranges": {
                param: {"min": data["min"].get(), "max": data["max"].get()}
                for param, data in self.param_ranges.items()
            },
        }
        try:
            with open(".deepmind_defaults", "wb") as f:  # Use a hidden file
                pickle.dump(settings, f)
        except Exception as e:
            CustomError(self, "Error", f"Failed to save settings: {e}")

    # Loads default settings from the ".deepmind_defaults" file
    # If the file doesn't exist, the application uses its built-in defaults
    def load_default_settings(self):
        try:
            with open(".deepmind_defaults", "rb") as f:
                settings = pickle.load(f)

            # Load device name.
            self.device_name.set(settings.get("device_name", "Deepmind12D"))

            # Load skip parameters (checkbox states).
            for param, value in settings.get("skip_params", {}).items():
                if param in self.skip_params:  # Check if the parameter still exists
                    self.skip_params[param].set(value)

            # Load parameter ranges.
            for param, data in settings.get("param_ranges", {}).items():
                if param in self.param_ranges:  # Check if the parameter still exists
                    self.param_ranges[param]["min"].set(data.get("min", 0))
                    self.param_ranges[param]["max"].set(
                        data.get("max", self.ranges[param])
                    )

        except FileNotFoundError:
            # If the file doesn't exist, use the built-in defaults (already set up)
            pass
        except Exception as e:
            CustomError(self, "Error", f"Failed to load settings: {e}")

    # Clears any custom default settings and reverts to the original application defaults
    # This also deletes the ".deepmind_defaults" file
    def clear_default_settings(self):

        # Reset device name
        self.device_name.set("Deepmind12D")

        # Reset skip parameters (checkboxes)
        for param in self.skip_params:
            self.skip_params[param].set(False)  # Default: not skipped (randomize)
        for param in [36, 37, 40, 43, 80, 82]:
            self.skip_params[param].set(True)  # Except for the initial skip list

        # Reset parameter ranges
        for param in self.param_ranges:
            self.param_ranges[param]["min"].set(0)
            self.param_ranges[param]["max"].set(self.ranges[param])

        # Delete the settings file
        try:
            import os

            os.remove(".deepmind_defaults")
        except FileNotFoundError:
            pass  # It's okay if the file doesn't exist
        except Exception as e:
            CustomError(self, "Error", f"Failed to clear settings: {e}")


if __name__ == "__main__":
    app = DeepMindRandomizer()
    app.mainloop()
