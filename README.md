# DeepMind 12D Randomizer

This script sends randomized NRPN values to the Behringer DeepMind 12D via Geert Bevin's super useful [SendMIDI command line tool](https://github.com/gbevin/SendMIDI). It will probably also work on the DeepMind 12 Keyboard version. 

Essentially, this script makes completely randomized patches, so some will be trash, and some might be interesting. Be aware that some randomizations may create loud patches and/or feedback loops.

**!!!!!!!!! Use this at your own risk !!!!!!!!!**

#### Requirements:
- [SendMIDIl](https://github.com/gbevin/SendMIDI)
- I think that's it

#### Usage:
- Check the midi device name for the DeepMind in your OS. On mac it defaults to "Deepmind 12D". If you've renamed yours, update line 78 with your one.
- Double-clicking the .sh will run a full randomization.*
- Alternatively, open Terminal and cd into the directory where you saved the script (eg. `cd /path/to/script/location`), then run `./DM12D-Randomizer.sh`. This will randomize all parameters in every section.*
- To randomize specific sections, use any or multiple of the following arguments:
  - -osc = Oscillators
  - -vca = VCA (Amp), VCA Envelopes, VCA Curves
  - -vcf = VCF (Filter), VCF Envelopes, VCF Curves
  - -env = VCA+VF+MOD Envelopes
  - -arp = Arpeggiator, Sequencer
  - -lfo = LFO section
  - -fx = FX types, mix, levels, modes, parameters
  - -mod = Mods Sources, Destinations, Depths
  - -poly = Voicing, Polyphony, Portamento

For example, you could run `./DM12D-Randomizer.sh -lfo -mod -fx` to randomize only the lfo, mod, and fx sections.

#### Notes:
- *I have omitted the following from randomization:
  - VCA Level (NRPN 80): 
    - Reason: To reduce likelihood of silent patches. 
    - Instead this will be set to 255.
  - VCA Highpass Freq (NRPN 40): 
    - Reason: To reduce likelihood of silent patches. 
    - Instead the existing value will remain.
  - VCA+VCF Envelope Velocity Sensitivities (NRPN 43, 82): 
    - Reason: To maintain playability. 
    - Instead the existing value will remain.
  - VCA Envelope Depth  (NRPN 42):
    - Reason: To maintain playability. 
    - Instead this will be set to 255.
  - Pitch bend Up+Down (NPRN 36, 37): 
    - Reason: To maintain playability. 
    - Instead these will be set to -24, +24.
- You can remove these from the skip list and/or add/remove other parameters in the relevant section toward the end of the script.

Enjoy!

#### Recognition / Credits:
Many thanks to [Geert Bevin](https://github.com/gbevin) for doing the hard work on SendMIDI.

