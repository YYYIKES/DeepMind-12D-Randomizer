#!/bin/bash

# =========================================================== #
#              Behringer DeepMind 12D Randomizer              #
#                          by YYYIKES!                        #
#                     yyyyyyyikes@gmail.com                   #
#                              ————                           #
#      https://github.com/YYYIKES/DeepMind-12D-Randomizer     #
# =========================================================== #

# ABOUT: ———————————————————————————————————————————————————— #
# 
# This script sends randomized NRPN values to the Behringer 
# DeepMind 12D via Geert Bevin's super useful SendMIDI command 
# line tool: https://github.com/gbevin/SendMIDI). 
# It will probably also work on the DM12 Keyboard version.
#
# Thanks to Geert Bevin for doing the hard work on SendMIDI,
# which can be found here: https://github.com/gbevin/SendMIDI

# REQUIREMENTS: ————————————————————————————————————————————— #
#
# - SendMIDI command line tool
# - I think that's it

# USAGE: ———————————————————————————————————————————————————— #
# 
# - Check the midi device name for the DeepMind in your OS. 
#   On mac it defaults to "Deepmind 12D". If you've renamed yours, 
#   update line 78 with your one.
# - Double-clicking the .sh will run a full randomization.*
# - Alternatively, open Terminal and cd into the directory where 
#   you saved the script (eg. `cd /path/to/script/location`), 
#   then run `./DM12D-Randomizer.sh`. This will randomize all 
#   parameters in every section.* To randomize specific sections, 
#   use any or multiple of the following arguments:
#     -osc = Oscillators
#     -vca = VCA (Amp), VCA Envelopes, VCA Curves
#     -vcf = VCF (Filter), VCF Envelopes, VCF Curves
#     -env = VCA+VF+MOD Envelopes
#     -arp = Arpeggiator, Sequencer
#     -lfo = LFO section
#     -fx = FX types, mix, levels, modes, parameters
#     -mod = Mods Sources, Destinations, Depths
#     -poly = Voicing, Polyphony, Portamento
#   eg. `./DM12D-Randomizer.sh -mod -arp`

# NOTES: ———————————————————————————————————————————————————— #
#
# * I have omitted the following from randomization:
#   - VCA Level (NRPN 80): 
#     Reason: To reduce likelihood of silent patches. 
#     Instead this will be set to 255.
#   - VCA Highpass Freq (NRPN 40): 
#     Reason: To reduce likelihood of silent patches. 
#     Instead the existing value will remain.
#   - VCA+VCF Envelope Velocity Sensitivities (NRPN 43, 82): 
#     Reason: To maintain playability. 
#     Instead the existing value will remain.
#   - Pitch bend Up+Down (NPRN 36, 37): 
#     Reason: To maintain playability. 
#     Instead these will be set to -24, +24.
#   You can remove these from the skip list and/or add/remove 
#   other parameters in the relevant section toward the end 
#   of the script.

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!                  Use at your own risk                   !!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


# ——————————————————————————————————————————————————————————— #


# START OF SCRIPT

# System name of your DeepMind midi device (mac defaults to 'Deepmind12D')
device="Deepmind12D"

# Create array of parameter maximum values in NRPN ascending order
ranges=(
  "255"  		# 00	LFO 1 Rate  (0-255)
  "255"  		# 01	LFO 1 Delay  (0-255)
  "6"    		# 02	LFO 1 Shape  (0-6)
  "1"    		# 03	LFO 1 Key Sync  (0-1)
  "1"    		# 04	LFO 1 Arp Sync  (0-1)
  "1"    		# 05	LFO 1 Mono Mode  (0-1)
  "255"  		# 06	LFO 1 Slew Rate  (0-255)
  "255"  		# 07	LFO 2 Rate  (0-255)
  "255"  		# 08	LFO 2 Delay / Fade  (0-255)
  "6"    		# 09	LFO 2 Shape  (0-6)
  "1"    		# 10	LFO 2 Key Sync  (0-1)
  "1"    		# 11	LFO 2 Arp Sync  (0-1)
  "255"  		# 12	LFO 2 Mono Mode  (0-255)
  "255"  		# 13	LFO 2 Slew Rate  (0-255)
  "2"    		# 14	OSC 1 Range  (0-2)
  "2"    		# 15	OSC 2 Range  (0-2)
  "5"    		# 16	OSC 1 PWM Source  (0-5)
  "5"    		# 17	OSC 2 Tone Mod Source  (0-5)
  "1"    		# 18	OSC 1 Pulse Enable  (0-1)
  "1"    		# 19	OSC 1 Saw Enable  (0-1)
  "1"    		# 20	OSC Sync Enable  (0-1)
  "255"  		# 21	OSC 1 Pitch Mod Depth  (0-255)
  "6"    		# 22	OSC 1 Pitch Mod Select  (0-6)
  "255"  		# 23	OSC 1 Aftertouch > Pitch Mod Depth  (0-255)
  "255"  		# 24	OSC 1 Mod Wheel > Pitch Mod Depth  (0-255)
  "255"  		# 25	OSC 1 PWM Depth  (0-255)
  "255"  		# 26	OSC 2 Level  (0-255)
  "255"  		# 27	OSC 2 Pitch  (0-255)
  "255"  		# 28	OSC 2 Tone Mod Depth  (0-255)
  "255"  		# 29	OSC 2 Pitch Mod Depth  (0-255)
  "255"  		# 30	OSC 2 Aftertouch > Pitch Mod Depth  (0-255)
  "255"  		# 31	OSC 2 Mod Wheel > Pitch Mod Depth  (0-255)
  "6"    		# 32	OSC 2 Pitch Mod Select  (0-6)
  "255"  		# 33	Noise Level  (0-255)
  "255"  		# 34	Portamento Time  (0-255)
  "13"   		# 35	Portamento Mode  (0-13)
  "24"  		# 36	Pitch bend Up depth  (0-48, default 46)
  "24"  		# 37	Pitch bend Down depth  (0-48, default 46)
  "1"    		# 38	OSC 1 Pitch Mod Mode  (0-1)
  "255"  		# 39	VCF Frequency  (0-255)
  "255" 		# 40	VCF Highpass Frequency  (0-255, default 0)
  "255"  		# 41	VCF Resonance  (0-255)
  "255"  		# 42	VCF Envelope Depth  (0-255)
  "255"  		# 43	VCF Envelope Velocity Sensitivity  (0-255, default 128)
  "255"  		# 44	VCF Pitch Bend to Freq Depth  (0-255)
  "255"  		# 45	VCF LFO Depth  (0-255)
  "1"    		# 46	VCF LFO Select  (0-1)
  "255"  		# 47	VCF Aftertouch > LFO Depth  (0-255)
  "255"  		# 48	VCF Mod Wheel > LFO Depth  (0-255)
  "255"  		# 49	VCF Keyboard Tracking  (0-255)
  "1"    		# 50	VCF Envelope Polarity  (0-1)
  "1"    		# 51	VCF 2 Pole Mode  (0-1)
  "1"    		# 52	VCF Bass Boost  (0-1)
  "255"  		# 53	VCA Envelope Attack Time  (0-255)
  "255"  		# 54	VCA Envelope Decay Time  (0-255)
  "255"  		# 55	VCA Envelope Sustain Level  (0-255)
  "255"  		# 56	VCA Envelope Release Time  (0-255)
  "4"    		# 57	VCA Envelope Trigger Mode  (0-4)
  "255"  		# 58	VCA Envelope Attack Curve  (0-255)
  "255"  		# 59	VCA Envelope Decay Curve  (0-255)
  "255"  		# 60	VCA Envelope Sustain Curve  (0-255)
  "255"  		# 61	VCA Envelope Release Curve  (0-255)
  "255"  		# 62	VCF Envelope Attack Time  (0-255)
  "255"  		# 63	VCF Envelope Decay Time  (0-255)
  "255"  		# 64	VCF Envelope Sustain Level  (0-255)
  "255"  		# 65	VCF Envelope Release Time  (0-255)
  "4"    		# 66	VCF Envelope Trigger Mode  (0-4)
  "255"  		# 67	VCF Envelope Attack Curve  (0-255)
  "255"  		# 68	VCF Envelope Decay Curve  (0-255)
  "255"  		# 69	VCF Envelope Sustain Curve  (0-255)
  "255"  		# 70	VCF Envelope Release Curve  (0-255)
  "255"  		# 71	Mod Envelope Attack Time  (0-255)
  "255"  		# 72	Mod Envelope Decay Time  (0-255)
  "255"  		# 73	Mod Envelope Sustain Level  (0-255)
  "255"  		# 74	Mod Envelope Release Time  (0-255)
  "4"    		# 75	Mod Envelope Trigger Mode  (0-4)
  "255"  		# 76	Mod Envelope Attack Curve  (0-255)
  "255"  		# 77	Mod Envelope Decay Curve  (0-255)
  "255"  		# 78	Mod Envelope Sustain Curve  (0-255)
  "255"  		# 79	Mod Envelope Release Curve  (0-255)
  "255" 		# 80 	VCA Level  (0-255, default 255)
  "255"  		# 81 	VCA Envelope Depth  (0-255)
  "255"  		# 82	VCA Envelope Velocity Sensitivity  (0-255, default 128)
  "255"  		# 83	VCA Pan Spread  (0-255)
  "2"    		# 84	Voice Priority Mode  (0-2)
  "12"   		# 85	Polyphony Mode  (0-12)
  "3"    		# 86	Envelope Trigger Mode  (0-3)
  "255"  		# 87	Unison Detune  (0-255)
  "255"  		# 88	Voice Drift  (0-255)
  "255"  		# 89	Parameter Drift  (0-255)
  "255"  		# 90	Drift Rate  (0-255)
  "255"  		# 91	OSC Portamento Balance  (0-255)
  "1"    		# 92	OSC Key Down Reset  (0-1)
  "22"   		# 93	Mod 1 Source  (0-22)
  "129"  		# 94	Mod 1 Destination  (0-129)
  "255"  		# 95	Mod 1 Depth  (0-255)
  "22"   		# 96	Mod 2 Source  (0-22)
  "129"  		# 97	Mod 2 Destination  (0-129)
  "255"  		# 98	Mod 2 Depth  (0-255)
  "22"   		# 99	Mod 3 Source  (0-22)
  "129"  		# 100	Mod 3 Destination  (0-129)
  "255"  		# 101	Mod 3 Depth  (0-255)
  "22"   		# 102	Mod 4 Source  (0-22)
  "129"  		# 103	Mod 4 Destination  (0-129)
  "255"  		# 104	Mod 4 Depth  (0-255)
  "22"   		# 105	Mod 5 Source  (0-22)
  "129"  		# 106	Mod 5 Destination  (0-129)
  "255"  		# 107	Mod 5 Depth  (0-255)
  "22"   		# 108	Mod 6 Source  (0-22)
  "129"  		# 109	Mod 6 Destination  (0-129)
  "255"  		# 110	Mod 6 Depth  (0-255)
  "22"   		# 111	Mod 7 Source  (0-22)
  "129"  		# 112	Mod 7 Destination  (0-129)
  "255"  		# 113	Mod 7 Depth  (0-255)
  "22"   		# 114	Mod 8 Source  (0-22)
  "129"  		# 115	Mod 8 Destination  (0-129)
  "255"  		# 116	Mod 8 Depth  (0-255)
  "1"    		# 117	Ctrl Sequencer Enable  (0-1)
  "15"   		# 118	Ctrl Sequencer Clock Divider  (0-15)
  "31"   		# 119	Sequence Length  (0-31)
  "25"   		# 120	Sequencer Swing Timing  (0-25)
  "2"    		# 121	Key Sync & Loop  (0-2)
  "255"  		# 122	Slew Rate  (0-255)
  "255"  		# 123	Seq Step Value 1  (0-255)
  "255"  		# 124	Seq Step Value 2  (0-255)
  "255"  		# 125	Seq Step Value 3  (0-255)
  "255"  		# 126	Seq Step Value 4  (0-255)
  "255"  		# 127	Seq Step Value 5  (0-255)
  "255"  		# 128	Seq Step Value 6  (0-255)
  "255"  		# 129	Seq Step Value 7  (0-255)
  "255"  		# 130	Seq Step Value 8  (0-255)
  "255"  		# 131	Seq Step Value 9  (0-255)
  "255"  		# 132	Seq Step Value 10  (0-255)
  "255"  		# 133	Seq Step Value 11  (0-255)
  "255"  		# 134	Seq Step Value 12  (0-255)
  "255"  		# 135	Seq Step Value 13  (0-255)
  "255"  		# 136	Seq Step Value 14  (0-255)
  "255"  		# 137	Seq Step Value 15  (0-255)
  "255"  		# 138	Seq Step Value 16  (0-255)
  "255" 		# 139	Seq Step Value 17  (0-255)
  "255"  		# 140	Seq Step Value 18  (0-255)
  "255"  		# 141	Seq Step Value 19  (0-255)
  "255"  		# 142	Seq Step Value 20  (0-255)
  "255"  		# 143	Seq Step Value 21  (0-255)
  "255"  		# 144	Seq Step Value 22  (0-255)
  "255"  		# 145	Seq Step Value 23  (0-255)
  "255"  		# 146	Seq Step Value 24  (0-255)
  "255"  		# 147	Seq Step Value 25  (0-255)
  "255"  		# 148	Seq Step Value 26  (0-255)
  "255"  		# 149	Seq Step Value 27  (0-255)
  "255"  		# 150	Seq Step Value 28  (0-255)
  "255"  		# 151	Seq Step Value 29  (0-255)
  "255"  		# 152	Seq Step Value 30  (0-255)
  "255"  		# 153	Seq Step Value 31  (0-255)
  "255"  		# 154	Seq Step Value 32  (0-255)
  "1"    		# 155	Arp On/Off  (0-1)
  "10"   		# 156	Arp Mode  (0-10)
  "255"  		# 157	Arp Rate (tempo)  (0-255)
  "12"   		# 158	Arp Clock  (0-12)
  "1"    		# 159	Arp Key Sync  (0-1)
  "255"  		# 160	Arp Gate Time  (0-255)
  "1"    		# 161	Arp Hold  (0-1)
  "64"   		# 162	Arp Pattern  (0-64)
  "25"   		# 163	Arp Swing  (0-25)
  "5"    		# 164	Arp Octaves  (0-5)
  "9"    		# 165	FX Routing  (0-9)
  "33"   		# 166	FX 1 Type  (0-33)
  "255"  		# 167	FX 1 Params 1  (0-255)
  "255"  		# 168	FX 1 Params 2  (0-255)
  "255"  		# 169	FX 1 Params 3  (0-255)
  "255"  		# 170	FX 1 Params 4  (0-255)
  "255"  		# 171	FX 1 Params 5  (0-255)
  "255"  		# 172	FX 1 Params 6  (0-255)
  "255"  		# 173	FX 1 Params 7  (0-255)
  "255"  		# 174	FX 1 Params 8  (0-255)
  "255"  		# 175	FX 1 Params 9  (0-255)
  "255"  		# 176	FX 1 Params 10  (0-255)
  "255"  		# 177	FX 1 Params 11  (0-255)
  "255"  		# 178	FX 1 Params 12  (0-255)
  "33"   		# 179	FX 2 Type  (0-33)
  "255"  		# 180	FX 2 Params 1  (0-255)
  "255"  		# 181	FX 2 Params 2  (0-255)
  "255"  		# 182	FX 2 Params 3  (0-255)
  "255"  		# 183	FX 2 Params 4  (0-255)
  "255"  		# 184	FX 2 Params 5  (0-255)
  "255"  		# 185	FX 2 Params 6  (0-255)
  "255"  		# 186	FX 2 Params 7  (0-255)
  "255"  		# 187	FX 2 Params 8  (0-255)
  "255"  		# 188	FX 2 Params 9  (0-255)
  "255"  		# 189	FX 2 Params 10  (0-255)
  "255"  		# 190	FX 2 Params 11  (0-255)
  "255"  		# 191	FX 2 Params 12  (0-255)
  "33"   		# 192	FX 3 Type  (0-33)
  "255"  		# 193	FX 3 Params 1  (0-255)
  "255"  		# 194	FX 3 Params 2  (0-255)
  "255"  		# 195	FX 3 Params 3  (0-255)
  "255"  		# 196	FX 3 Params 4  (0-255)
  "255"  		# 197	FX 3 Params 5  (0-255)
  "255"  		# 198	FX 3 Params 6  (0-255)
  "255"  		# 199	FX 3 Params 7  (0-255)
  "255"  		# 200	FX 3 Params 8  (0-255)
  "255"  		# 201	FX 3 Params 9  (0-255)
  "255"  		# 202	FX 3 Params 10  (0-255)
  "255"  		# 203	FX 3 Params 11  (0-255)
  "255"  		# 204	FX 3 Params 12  (0-255)
  "33"   		# 205	FX 4 Type  (0-33)
  "255"  		# 206	FX 4 Params 1  (0-255)
  "255"  		# 207	FX 4 Params 2  (0-255)
  "255"  		# 208	FX 4 Params 3  (0-255)
  "255"  		# 209	FX 4 Params 4  (0-255)
  "255"  		# 210	FX 4 Params 5  (0-255)
  "255"  		# 211	FX 4 Params 6  (0-255)
  "255"  		# 212	FX 4 Params 7  (0-255)
  "255"  		# 213	FX 4 Params 8  (0-255)
  "255"  		# 214	FX 4 Params 9  (0-255)
  "255"  		# 215	FX 4 Params 10  (0-255)
  "255"  		# 216	FX 4 Params 11  (0-255)
  "255"  		# 217	FX 4 Params 12  (0-255)
  "150"  		# 218	FX 1 Output Gain  (0-150)
  "150" 		# 219	FX 2 Output Gain  (0-150)
  "150" 		# 220	FX 3 Output Gain  (0-150)
  "150"  		# 221	FX 4 Output Gain  (0-150)
  "2"    		# 222	FX Mode  (0-2)
)

# Define parameter groups
param_groups_osc="14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 38 91 92"
param_groups_vca="53 54 55 56 57 58 59 60 61 80 81 82 83"
param_groups_vcf="39 40 41 42 43 44 45 46 47 48 49 50 51 52 62 63 64 65 66 67 68 69 70"
param_groups_env="53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79"
param_groups_arp="117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164"
param_groups_lfo="0 1 2 3 4 5 6 7 8 9 10 11 12 13"
param_groups_fx="165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222"
param_groups_mod="71 72 73 74 75 76 77 78 79 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116"
param_groups_poly="34 35 36 37 84 85 86 87 88 89 90 91 92"


# Parameters to skip from randomization
params_to_skip=(
    36    # Pitch bend Up depth
    37    # Pitch bend Down depth
    40    # VCF Highpass Frequency
    43    # VCF Envelope Velocity Sensitivity
    80    # VCA Level
    82    # VCA Envelope Velocity Sensitivity
)

# Helper function to randomize parameters
randomize_params() {
  local params=("$@")
    for nrpn in "${params[@]}"; do
        
        # Check if the current NRPN is in the skip list
        skip=false
        for skip_nrpn in "${params_to_skip[@]}"; do
          if [ "$nrpn" -eq "$skip_nrpn" ]; then
            skip=true
            break
          fi
        done

        if $skip; then
            # Here you can add a value if a default value needs to be set
            if [ "$nrpn" -eq "36" ] || [ "$nrpn" -eq "37" ]
            then
                 sendmidi dev "$device" NRPN "$nrpn" "48"
            elif [ "$nrpn" -eq "80" ]
            then
             sendmidi dev "$device" NRPN "$nrpn" "255"
            fi
          
            continue  # Skip to the next NRPN if it's in the skip list
        fi
        
      # Randomize NRPN values and send to DeepMind
      max="${ranges[$nrpn]}"
      random_value=$((RANDOM % (max + 1)))
      sendmidi dev "$device" NRPN "$nrpn" "$random_value"
  done
}

# Check if any arguments were passed
if [ $# -eq 0 ]; then
  # If no arguments, randomize all parameters
  echo "Randomizing. Please wait..."
  randomize_params $(seq 0 $((${#ranges[@]}-1)))
else
  # If arguments, loop through them and randomize specified parameter groups
  echo "Randomizing. Please wait..."
  for arg in "$@"; do
      case "$arg" in
          -osc) randomize_params $param_groups_osc ;;
          -vca) randomize_params $param_groups_vca ;;
          -vcf) randomize_params $param_groups_vcf ;;
          -env) randomize_params $param_groups_env ;;
          -arp) randomize_params $param_groups_arp ;;
          -lfo) randomize_params $param_groups_lfo ;;
          -fx) randomize_params $param_groups_fx ;;
          -mod) randomize_params $param_groups_mod ;;
          -poly) randomize_params $param_groups_poly ;;
          *) echo "Invalid argument: $arg" ;;
      esac
  done
fi

echo "Done!"
