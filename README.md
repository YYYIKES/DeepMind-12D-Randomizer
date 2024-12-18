# DeepMind 12D Randomizer

This script sends randomized NRPN values to the Behringer DeepMind 12D via Geert Bevin's super useful [SendMIDI command line tool](https://github.com/gbevin/SendMIDI). It will probably also work on the DeepMind 12 Keyboard version. 

Essentially, this script makes completely randomized patches, so some will be trash, and some might be interesting. Be aware that some randomizations may create loud patches and/or feedback loops.

**!! Use this at your own risk. I'm not a real coder. I'm just some guy !!**

#### Requirements
- SendMIDI command like tool
- I think that's it

#### Usage
- Check the midi device name for the DeepMind in your OS. On mac it defaults to "DeepMind 12D". If you've renamed yours, update line 59 with your one.
- Double-clicking the .sh will run a full randomization.*
- Alternatively, open Terminal and cd into the directory you saved the script (`cd /path/to/script/location`), then run `./DM12D-Randomizer.sh`. This will randomize all parameters in every section.* To randomize specific sections, use any or multiple of the following arguments:
  - -o = Oscillators
  - -f = VCF (Filter), VCF Envelopes, VCF Curves
  - -a = VCA (Amp), VCA Envelopes, VCA Curves
  - -m = Mods Sources, Destinations, Depths
  - -v = Voicing, Polyphony, Portamento
  - -r = Arpeggiator, Sequences
  - -fx = FX types, mix, levels, modes, parameters
 
For example, you could run `./DM12D-Randomizer.sh -l -m -fx` to randomize only the lfo, mod, and fx sections.

_* I have omitted the following from randomization to reduce the chance of silent patches, and retain default pitch bend settings: VCA Level (NRPN 80), VCF Highpass Frequency (NRPN 40), Pitch bend Up (NPRN 36), and Pitch bend Down (NPRN 37). These are defined in $ranges, so you can add the NRPN numbers to the relevant $param_group if needed._

#### Recognition / Credits
Many thanks to [Geert Bevin](https://github.com/gbevin) for doing the hard work on SendMIDI.

