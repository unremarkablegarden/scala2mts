# 𝕾𝖈𝖆𝖑𝖆 𝟐 𝕸𝕿𝕾

**Scala2MTS** is a Python program to convert **Scala** tuning files to **MIDI Tuning Standard SysEx** (for use with hardware synths and sequencers, like the *[Sequentix Cirklon](https://www.sequentix.com/)* and *[Sequential Prophet rev2](https://www.sequential.com/product/prophetrev2/)*).

Works with Scala files defined in *[just intonation](https://www.kylegann.com/tuning.html)* (ratios) or in *cents*. Works with [non-2/1 octave tunings](https://en.xen.wiki/w/Bohlen-Pierce_scale) and non-octave-repeating tunings, for the real headz.

I made this because I just couldn't find a tool that does it online any more, and because the SysEx dumps from the [Scala app](https://huygens-fokker.org/scala/) itself are the wrong formats to be able to specify a program memory slot with [HexFiend](https://hexfiend.com/) after *(Yes, I tried them all)*.

You can use [SysEx Librarian](https://www.snoize.com/sysexlibrarian/) to transfer the tunings to your devices.

Shoutouts to *[Kraig Grady](https://anaphoria.bandcamp.com/music)* for making my favorite tunings (like **[Sisiutl](https://www.anaphoria.com/centaur.html)**), to *[I Nyoman Mariyana](https://www.instagram.com/mangbosski/)* for showing me his ancient Balinese gamelan tunings and being the reason to make this script, and to *[Werner Durand](https://wernerdurand.bandcamp.com/)* for deepening my knowledge and love for microtonality.

If you found this project useful consider [donating](https://www.paypal.com/donate/?hosted_button_id=ZYM99298H3T2Y) 🙏

# [𝕾𝖈𝖆𝖑𝖆𝟐𝕸𝕿𝕾 (web app)](https://scala2mts.vercel.app/)

![Scala2MTS web](https://raw.githubusercontent.com/unremarkablegarden/scala2mts/main/screenshots/web-app.png)

# 𝖀𝖘𝖆𝖌𝖊 (binary)

![Scala2MTS](https://raw.githubusercontent.com/unremarkablegarden/scala2mts/main/screenshots/GUI%20v0.0.4.png)

Currently I've only compiled the GUI version for Apple Silicon Macs. Run it from the terminal after making it executable first.

First download it from Releases in the left sidebar here on GitHub.

```
cd ~/path/to/scala2mts
chmod +x scala2mts
./scala2mts
```

This will give you the macOS error message:

`“scala2mts” can’t be opened because Apple cannot check it for malicious software.`

* Open System Settings > Privacy & Security
* Scroll down to where you see `"scala2mts" was blocked from use because it is not from an identified developer`
* Click the button `Allow Anyway`
* Either: In the terminal again: `./scala2mts`
* Or: Just double-click on the executable in Finder


# 𝖀𝖘𝖆𝖌𝖊 (compiling for Linux, Windows, etc.)

You can compile it for your platform with Python by installing `pyinstaller` with `pip`, and then running:

> pyinstaller --onefile scala2mts-gui.py


# 𝖀𝖘𝖆𝖌𝖊 (command line)

> python scala2mts.py -h

```
Convert Scala files to SysEx files for use with the Prophet rev2 and Cirklon.
MTS - MIDI Tuning standard 1.0

(Works with scala files that use ratios or cents)

Arguments:
-i input file: the Scala file to convert
-o output file: the SysEx file to create (default: the input file name with .syx extension)
-n base_note: the base note as a number (default = 69 = A4)
-f base_freq: the base frequency of the Scala file (default = 440.000)
-p program_number: which memory slot to store the tuning in the synth
-h help: show this help message
```

> python scala2mts.py -i grady-sisiutl.scl -n 48 -f 298 -p 7

```
Base note: 48
Base freq: 298.0
Notes per octave: 12
————————————————————
Intervals
1 = 62.961
2 = 203.91
3 = 266.871
4 = 417.508
5 = 498.045
6 = 551.318
7 = 701.955
8 = 764.916
9 = 915.553
10 = 968.826
11 = 1049.363
12 = 1200.0
————————————————————
F07E 0008 0106 6772 6164 7920 7369 6369 7574 696c 2020 0e20 000e 7051
1025 0f10 7561 1237 0513 1d38 1362 4715 2247 1573 1917 343d 1778 2818
6000 1a20 001a 7051 1c25 0f1c 7561 1e37 051f 1d38 1f62 4721 2247 2173
1923 343d 2378 2824 6000 2620 0026 7051 2825 0f28 7561 2a37 052b 1d38
2b62 472d 2247 2d73 192f 343d 2f78 2830 6000 3220 0032 7051 3425 0f34
7561 3637 0537 1d38 3762 4739 2247 3973 193b 343d 3b78 283c 6000 3e20
003e 7051 4025 0f40 7561 4237 0543 1d38 4362 4745 2247 4573 1947 343d
4778 2848 6000 4a20 004a 7051 4c25 0f4c 7561 4e37 054f 1d38 4f62 4751
2247 5173 1953 343d 5378 2854 6000 5620 0056 7051 5825 0f58 7561 5a37
055b 1d38 5b62 475d 2247 5d73 195f 343d 5f78 2860 6000 6220 0062 7051
6425 0f64 7561 6637 0567 1d38 6762 4769 2247 6973 196b 343d 6b78 286c
6000 6e20 006e 7051 7025 0f70 7561 7237 0573 1d38 7362 4775 2247 7573
1977 343d 7778 2878 6000 7a20 007a 7051 7c25 0f7c 7561 7e37 057f 0000
7f00 007f 0000 7f00 007f 0000 7f00 007f 0000 7f00 007f 0000 7f00 007f
0000 7f00 007f 0000 7f00 007f 0000 01F7
————————————————————

Output file grady-sisiutl.syx already exists. Overwrite? (y/n)
y
Wrote sysex to grady-sisiutl.syx
```

# 𝕽𝖊𝖖𝖚𝖎𝖗𝖊𝖒𝖊𝖓𝖙𝖘
* `Python 3`
* `tkinter` for running the non-binary GUI version

—

# 𝕷𝖎𝖓𝖐𝖘
* Moon Wheel — [Soundcloud](https://soundcloud.com/moonwheel), [Bandcamp](https://moonwheel.bandcamp.com/)
* Tusagi — [Soundcloud](https://soundcloud.com/tusagi)
* [Scale Workshop](https://sevish.com/scaleworkshop/)
* [Scala tunings archive (5100, ZIP)](https://huygens-fokker.org/docs/scales.zip)
* [Scala tunings archive descriptions](https://huygens-fokker.org/docs/scalesdir.txt)
* [Xenharmonic Alliance: Microtonal Music Forum](https://www.facebook.com/groups/476404232379884)
* [Cirklon forum](http://forum.sequentix.com/viewforum.php?f=1)

—

🪦 *RIP https://www.microtonalsoftware.com/scl-scala-to-mts-converter.html* 🪦
