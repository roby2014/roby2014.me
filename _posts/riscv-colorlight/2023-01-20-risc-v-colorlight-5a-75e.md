---
layout: post
title: Hacking Colorlight 5A-75E - Implementing a RISC-V soft core into a 15$ FPGA board.
date: 2023-01-20 01:00 +0700
modified: 2023-01-20 01:00 +0700
description: Demonstration on using a soft core (VexRiscv) built with LiTex in a Colorlight 5A-75E board (Lattice ECP5 FPGA).
tag:
  - fpga
  - ecp5
  - colorlight
  - riscv
  - vexriscv
  - litex
  - oss
  - ft232rl
  - ftdi
  - uart
image: /programming-colorlight-ecp5/board.png
---

- [Introduction](#introduction)
- [Setup](#setup)
- [References](#references)

### Introduction

So in the previous post I showed you how you can program a **Colorlight 5A-75E** board with **open source tools** and using **FT232RL** chip as **JTAG** programmer. 

In this post, we'll continue this adventure, by implementing a RISC-V soft core ([**VexRiscv**](https://github.com/SpinalHDL/VexRiscv)) built with [**LiTex**]((https://github.com/enjoy-digital/litex)).


### Setup

I have prepared a quick setup on [my repository (roby2014/risc-v-colorlight-5a-75e)](https://github.com/roby2014/risc-v-colorlight-5a-75e). The repository contains all the steps/commands that you need. 
```bash
git clone https://github.com/roby2014/risc-v-colorlight-5a-75e
cd risc-v-colorlight-5a-75e
```

There is not much to say here... Read the repository's `readme.md` like you would read the blog post. Everything should be well documented and easy to understand.

### References
- [roby2014/risc-v-colorlight-5a-75e](https://github.com/roby2014/risc-v-colorlight-5a-75e)
