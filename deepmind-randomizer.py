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
            255,
            255,
            6,
            1,
            1,
            1,
            255,
            255,
            255,
            6,
            1,
            1,
            255,
            255,
            2,
            2,
            5,
            5,
            1,
            1,
            1,
            255,
            6,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            6,
            255,
            255,
            13,
            24,
            24,
            1,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            1,
            255,
            255,
            255,
            1,
            1,
            1,
            255,
            255,
            255,
            255,
            4,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            4,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            4,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            2,
            12,
            3,
            255,
            255,
            255,
            255,
            255,
            1,
            22,
            129,
            255,
            22,
            129,
            255,
            22,
            129,
            255,
            22,
            129,
            255,
            22,
            129,
            255,
            22,
            129,
            255,
            22,
            129,
            255,
            22,
            129,
            255,
            1,
            15,
            31,
            25,
            2,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            1,
            10,
            255,
            12,
            1,
            255,
            1,
            64,
            25,
            5,
            9,
            33,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            33,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            33,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            33,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            150,
            150,
            150,
            150,
            2,
        ]

        # Parameter groups: Organizes parameters into logical sections
        self.param_groups = {
            "OSC": [
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
                31,
                32,
                33,
                38,
                91,
                92,
            ],
            "VCA": [53, 54, 55, 56, 57, 58, 59, 60, 61, 80, 81, 82, 83],
            "VCF": [
                39,
                40,
                41,
                42,
                43,
                44,
                45,
                46,
                47,
                48,
                49,
                50,
                51,
                52,
                62,
                63,
                64,
                65,
                66,
                67,
                68,
                69,
                70,
            ],
            "ENV": [
                53,
                54,
                55,
                56,
                57,
                58,
                59,
                60,
                61,
                62,
                63,
                64,
                65,
                66,
                67,
                68,
                69,
                70,
                71,
                72,
                73,
                74,
                75,
                76,
                77,
                78,
                79,
            ],
            "ARP/SEQ": [
                117,
                118,
                119,
                120,
                121,
                122,
                123,
                124,
                125,
                126,
                127,
                128,
                129,
                130,
                131,
                132,
                133,
                134,
                135,
                136,
                137,
                138,
                139,
                140,
                141,
                142,
                143,
                144,
                145,
                146,
                147,
                148,
                149,
                150,
                151,
                152,
                153,
                154,
                155,
                156,
                157,
                158,
                159,
                160,
                161,
                162,
                163,
                164,
            ],
            "LFO": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "FX": [
                165,
                166,
                167,
                168,
                169,
                170,
                171,
                172,
                173,
                174,
                175,
                176,
                177,
                178,
                179,
                180,
                181,
                182,
                183,
                184,
                185,
                186,
                187,
                188,
                189,
                190,
                191,
                192,
                193,
                194,
                195,
                196,
                197,
                198,
                199,
                200,
                201,
                202,
                203,
                204,
                205,
                206,
                207,
                208,
                209,
                210,
                211,
                212,
                213,
                214,
                215,
                216,
                217,
                218,
                219,
                220,
                221,
                222,
            ],
            "MOD": [
                71,
                72,
                73,
                74,
                75,
                76,
                77,
                78,
                79,
                93,
                94,
                95,
                96,
                97,
                98,
                99,
                100,
                101,
                102,
                103,
                104,
                105,
                106,
                107,
                108,
                109,
                110,
                111,
                112,
                113,
                114,
                115,
                116,
            ],
            "POLY": [34, 35, 36, 37, 84, 85, 86, 87, 88, 89, 90, 91, 92],
        }

        # Parameter names: Maps parameter numbers to human-readable names
        self.param_names = {
            0: "LFO1 Rate",
            1: "LFO1 Delay",
            2: "LFO1 Shape",
            3: "LFO1 Key Sync",
            4: "LFO1 Arp Sync",
            5: "LFO1 Mono Mode",
            6: "LFO1 Slew",
            7: "LFO2 Rate",
            8: "LFO2 Delay",
            9: "LFO2 Shape",
            10: "LFO2 Key Sync",
            11: "LFO2 Arp Sync",
            12: "LFO2 Mono Mode",
            13: "LFO2 Slew",
            14: "OSC1 Range",
            15: "OSC2 Range",
            16: "OSC1 PWM Src",
            17: "OSC2 TM Src",
            18: "OSC1 Pulse",
            19: "OSC1 Saw",
            20: "OSC Sync",
            21: "OSC1 PM Depth",
            22: "OSC1 PM Select",
            23: "OSC1 ATouch>PM Depth",
            24: "OSC1 MW>PM Depth",
            25: "OSC1 PWM Depth",
            26: "OSC2 Level",
            27: "OSC2 Pitch",
            28: "OSC2 TM Depth",
            29: "OSC2 PM Depth",
            30: "OSC2 ATouch>PM Depth",
            31: "OSC2 MW>PM Depth",
            32: "OSC2 PM Select",
            33: "Noise Level",
            34: "Porta Time",
            35: "Porta Mode",
            36: "PB+ Depth",
            37: "PB- Depth",
            38: "OSC1 PM Mode",
            39: "VCF Freq",
            40: "VCF HPF",
            41: "VCF Reso",
            42: "VCF Env Depth",
            43: "VCF Env Velo Sens",
            44: "VCF PB>Freq Depth",
            45: "VCF LFO Depth",
            46: "VCF LFO Select",
            47: "VCF ATouch>LFO Depth",
            48: "VCF MW>LFO Depth",
            49: "VCF Keytrack",
            50: "VCF Env Polarity",
            51: "VCF 2 Pole",
            52: "VCF Boost",
            53: "VCA Env Atk",
            54: "VCA Env Dec",
            55: "VCA Env Sust",
            56: "VCA Env Rel",
            57: "VCA Env Trig Mode",
            58: "VCA Env Atk Curve",
            59: "VCA Env Dec Curve",
            60: "VCA Env Sust Curve",
            61: "VCA Env Rrel Curve",
            62: "VCF Env Atk",
            63: "VCF Env Dec",
            64: "VCF Env Sust",
            65: "VCF Env Rel",
            66: "VCF Env Trig Mode",
            67: "VCF Env Atk Curve",
            68: "VCF Env Dec Curve",
            69: "VCF Env Sust Curve",
            70: "VCF Env Rel Curve",
            71: "Mod Env Atk",
            72: "Mod Env Dec",
            73: "Mod Env Sust",
            74: "Mod Env Rel",
            75: "Mod Env Trig Mode",
            76: "Mod Env Atk Curve",
            77: "Mod Env Dec Curve",
            78: "Mod Env Sust Curve",
            79: "Mod Env Rel Curve",
            80: "VCA Level",
            81: "VCA Env Depth",
            82: "VCA Env Velo Sens",
            83: "VCA Pan Spread",
            84: "Voice Priority Mode",
            85: "Polyphony Mode",
            86: "Env Trigger Mode",
            87: "Unison Detune",
            88: "Voice Drift",
            89: "Parameter Drift",
            90: "Drift Rate",
            91: "OSC Porta Balance",
            92: "OSC Key Reset",
            93: "Mod1 Src",
            94: "Mod1 Dest",
            95: "Mod1 Depth",
            96: "Mod2 Src",
            97: "Mod2 Dest",
            98: "Mod2 Depth",
            99: "Mod3 Src",
            100: "Mod3 Dest",
            101: "Mod3 Depth",
            102: "Mod4 Src",
            103: "Mod4 Dest",
            104: "Mod4 Depth",
            105: "Mod5 Src",
            106: "Mod5 Dest",
            107: "Mod5 Depth",
            108: "Mod6 Src",
            109: "Mod6 Dest",
            110: "Mod6 Depth",
            111: "Mod7 Src",
            112: "Mod7 Dest",
            113: "Mod7 Depth",
            114: "Mod8 Src",
            115: "Mod8 Dest",
            116: "Mod8 Depth",
            117: "Ctrl Seq Enable",
            118: "Ctrl Seq Clock",
            119: "Sequence Length",
            120: "Sequencer Swing",
            121: "Key Sync & Loop",
            122: "Slew",
            123: "Seq Step 1",
            124: "Seq Step 2",
            125: "Seq Step 3",
            126: "Seq Step 4",
            127: "Seq Step 5",
            128: "Seq Step 6",
            129: "Seq Step 7",
            130: "Seq Step 8",
            131: "Seq Step 9",
            132: "Seq Step 10",
            133: "Seq Step 11",
            134: "Seq Step 12",
            135: "Seq Step 13",
            136: "Seq Step 14",
            137: "Seq Step 15",
            138: "Seq Step 16",
            139: "Seq Step 17",
            140: "Seq Step 18",
            141: "Seq Step 19",
            142: "Seq Step 20",
            143: "Seq Step 21",
            144: "Seq Step 22",
            145: "Seq Step 23",
            146: "Seq Step 24",
            147: "Seq Step 25",
            148: "Seq Step 26",
            149: "Seq Step 27",
            150: "Seq Step 28",
            151: "Seq Step 29",
            152: "Seq Step 30",
            153: "Seq Step 31",
            154: "Seq Step 32",
            155: "Arp On/Off",
            156: "Arp Mode",
            157: "Arp Rate",
            158: "Arp Clock",
            159: "Arp Key Sync",
            160: "Arp Gate",
            161: "Arp Hold",
            162: "Arp Pattern",
            163: "Arp Swing",
            164: "Arp Octaves",
            165: "FX Routing",
            166: "FX1 Type",
            167: "FX1 Param 1",
            168: "FX1 Param 2",
            169: "FX1 Param 3",
            170: "FX1 Param 4",
            171: "FX1 Param 5",
            172: "FX1 Param 6",
            173: "FX1 Param 7",
            174: "FX1 Param 8",
            175: "FX1 Param 9",
            176: "FX1 Param 10",
            177: "FX1 Param 11",
            178: "FX1 Param 12",
            179: "FX2 Type",
            180: "FX2 Param 1",
            181: "FX2 Param 2",
            182: "FX2 Param 3",
            183: "FX2 Param 4",
            184: "FX2 Param 5",
            185: "FX2 Param 6",
            186: "FX2 Param 7",
            187: "FX2 Param 8",
            188: "FX2 Param 9",
            189: "FX2 Param 10",
            190: "FX2 Param 11",
            191: "FX2 Param 12",
            192: "FX3 Type",
            193: "FX3 Param 1",
            194: "FX3 Param 2",
            195: "FX3 Param 3",
            196: "FX3 Param 4",
            197: "FX3 Param 5",
            198: "FX3 Param 6",
            199: "FX3 Param 7",
            200: "FX3 Param 8",
            201: "FX3 Param 9",
            202: "FX3 Param 10",
            203: "FX3 Param 11",
            204: "FX3 Param 12",
            205: "FX4 Type",
            206: "FX4 Param 1",
            207: "FX4 Param 2",
            208: "FX4 Param 3",
            209: "FX4 Param 4",
            210: "FX4 Param 5",
            211: "FX4 Param 6",
            212: "FX4 Param 7",
            213: "FX4 Param 8",
            214: "FX4 Param 9",
            215: "FX4 Param 10",
            216: "FX4 Param 11",
            217: "FX4 Param 12",
            218: "FX1 Gain",
            219: "FX2 Gain",
            220: "FX3 Gain",
            221: "FX4 Gain",
            222: "FX Mode",
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
                should_skip = param in [36, 37, 40, 43, 80, 82]
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
