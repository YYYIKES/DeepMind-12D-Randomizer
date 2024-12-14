# DeepMind 12D Randomizer

This bash script sends randomized NRPN values (within their min and max ranges) to the DeepMind 12D using the super useful SendMIDI command like tool

Essentially, this script makes completely randomized patches, so some will be trash, and some might be interesting. The inline comments show the NRPR number, Parameter Name, and the min and max values of each parameter. To return any parameters to their defaults (or specific value), add them to the relevant section toward the end of the script. For example, currently the script will return the VCA Level and High Pass Filter to their defaults to reduce the likelihood of completely silent patches. So far I've made some interesting patches by running the randomizer, then kind-of dialing back the outrageous stuff until I like what I hear.

#### Requirements
- [SendMIDI command like tool](https://github.com/gbevin/SendMIDI)
- I guess Homebrew
- I think that's it

#### Usage
1. Download `DM12D-Randomizer.sh`
2. Install SendMIDI according to the [instructions](https://github.com/gbevin/SendMIDI?tab=readme-ov-file#download), eg. via Homebrew by running `brew install gbevin/tools/sendmidi`
3. Run `DM12D-Randomizer.sh` by double-clicking or via Terminal

#### Notes
- Use this at your own risk. I'm not a coder by trade.
- This will probably work for the DeepMind 12 keyboard model too.
- If anyone has any suggestions to make the script more efficient let me know! I'm not a coder by trade.

#### Thanks
Thanks to Geert Bevin for doing the hard work with his SendMIDI tool.

