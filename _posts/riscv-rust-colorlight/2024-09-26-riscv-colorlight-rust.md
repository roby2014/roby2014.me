---
layout: post
title: Hacking Colorlight 5A-75E - Running Rust 🦀 firmware on a RISC-V SoC!
date: 2024-07-26 01:00 +0700
modified: 2024-07-20 01:00 +0700
description: Hacking a Chinese LED display board with open-source FPGA tools, RISC-V and Rust 🦀 
tag:
  - rust
  - fpga
  - ecp5
  - colorlight
  - riscv
  - litex
  - oss
  - uart
  - pac
image: /riscv-rust-colorlight-ecp5/embedded-ferris-soldering.png
---

- [Introduction](#introduction)
- [Building the RISC-V SoC](#building-the-risc-v-SoC)
- [Flashing FPGA](#flashing-fpga)
- [Peripheral Access Crate (PAC)](#peripheral-access-crate-pac)
- [Firmware](#firmware)
- [Conclusion](#conclusion)

![embedded-ferris-soldering](./embedded-ferris-soldering.png)

### Introduction

In my previous posts, I demonstrated how to [flash a custom bitstream](https://roby2014-me.vercel.app/programming-a-colorlight-5a-75e-board-ECP5-FPGA-with-open-source-tools/) onto the **Colorlight 5A-75E** (ECP5 FPGA) board using **open-source tools** and the **FT232RL** chip as a **JTAG programmer**. We also explored [integrating a RISC-V SoC](https://roby2014-me.vercel.app/risc-v-colorlight-5a-75e/) (built with [LiteX](https://github.com/enjoy-digital/litex)) with custom [C firmware](https://github.com/roby2014/risc-v-colorlight-5a-75e/blob/master/firmware/main.c).

In this post, we’ll take things a step further and dive deeper. This time, we’ll be building and running **Rust 🦀 firmware** on the RISC-V SoC, continuing the adventure into the world of **FPGA hacking** and **open-source tools**.

*I wont enter in much details about LiteX or Rust, but I’ll provide an overview of how this process works and can be done. Be sure to follow along with my repository: [https://github.com/roby2014/colorlight-riscv-rs/](https://github.com/roby2014/colorlight-riscv-rs/).*

### Building the RISC-V SoC

The heart of this project is turning the Colorlight 5A-75E board into a simple RISC-V SoC using [LiteX](https://github.com/enjoy-digital/litex), which provides an open-source framework for building SoCs on FPGAs.

With a simple [script](https://github.com/roby2014/colorlight-riscv-rs/blob/main/soc.py), you can build a full RISC-V SoC ready to flash your FPGA and run custom firmware on it.

*(For more in-depth information, check out LiteX documentation.)*

So, for building SoC bitstream and dependencies for later:
```bash
python3 soc.py --build --cpu-type vexriscv --csr-svd "./litex-pac/5a-75e_6.0.svd"
```
- `5a-75e_6.0.svd` will be overwritten and used later for the LiteX PAC (Peripheral Access Crate).
- You can try and use `--memory-x "../litex-pac/memory.x"`, however, I encountered many issues with the provided memory file, so I created my own one around `regions.ld` (see #firmware).

### Flashing FPGA

After building the bitstream, flashing the FPGA should be easy as:
```bash
python3 soc.py --load --no-compile-software
```

### Peripheral Access Crate (PAC)

When building the SoC, LiteX will generate the `svd` file (representation of the hardware peripherals and their registers). With this, [`svd2rust`](https://github.com/rust-embedded/svd2rust) can be used to create the PAC in order to access and manipulate the system with Rust bindings. The PAC will use its `build.rs` to do this automatically. A pre-generated PAC can be found in the [repository `litex-pac` folder](https://github.com/roby2014/colorlight-riscv-rs/tree/main/litex-pac).

Simple example of how the `.svd` file looks:
```svd
    <peripherals>
        <peripheral>
            <name>CTRL</name>
            <baseAddress>0xF0000000</baseAddress>
            <groupName>CTRL</groupName>
            <registers>
                <register>
                    <name>RESET</name>
                    <addressOffset>0x0000</addressOffset>
                    <resetValue>0x00</resetValue>
                    <size>32</size>
                    <fields>
                        <field>
                            <name>soc_rst</name>
                            <msb>0</msb>
                            <bitRange>[0:0]</bitRange>
                            <lsb>0</lsb>
                            <description><![CDATA[Write `1` to this register to reset the full SoC (Pulse Reset)]]></description>
                        </field>

                        .....
```

### Firmware

Firmware is built after SoC is also built, because it will depend on the memory regions defined at `regions.ld` (generated by LiteX).

After that, we can create the following files:
- `firmware/memory.x` (defines memory regions and interrupt handlers):
  ```
  REGION_ALIAS("REGION_TEXT", main_ram);
  REGION_ALIAS("REGION_RODATA", main_ram);
  REGION_ALIAS("REGION_DATA", main_ram);
  REGION_ALIAS("REGION_BSS", sram);
  REGION_ALIAS("REGION_HEAP", sram);
  REGION_ALIAS("REGION_STACK", sram);

  PROVIDE(uart = DefaultHandler);
  PROVIDE(timer0 = DefaultHandler);
  ```
- `firmware/build.rs` (when `memory.x` or `regions.ld` change, rebuilds and put the linker script somewhere the linker can find it (with `firmware/.cargo/config`):
  ```rs
  use std::env;
  use std::fs::File;
  use std::io::Write;
  use std::path::Path;

  /// Put the linker script somewhere the linker can find it.
  fn main() {
    let out_dir = env::var("OUT_DIR").expect("No out dir");
    let dest_path = Path::new(&out_dir);

    let mut f = File::create(&dest_path.join("memory.x")).expect("Could not create file");
    f.write_all(include_bytes!("memory.x"))
        .expect("Could not write file");

    let mut f = File::create(&dest_path.join("regions.ld")).expect("Could not create file");
    f.write_all(include_bytes!(concat!(
        env!("BUILD_DIR"),
        "/software/include/generated/regions.ld"
    )))
    .expect("Could not write file");

    println!("cargo:rustc-link-search={}", dest_path.display());

    println!("cargo:rerun-if-changed=regions.ld");
    println!("cargo:rerun-if-changed=memory.x");
    println!("cargo:rerun-if-changed=build.rs");
  }
  ```

On the dependencies side, we need a RISC-V runtime, panic halt and the generated PAC Rust bindings.

```toml
[dependencies]
riscv-rt = "0.12.0"
panic-halt = "0.2.0"
litex-pac = { path = "../litex-pac" } # use pac
```

Below is a simple example of Rust firmware for the RISC-V SoC, which continuously sends "hello" through the UART (serial) interface.

```rust
#![no_std]
#![no_main]

extern crate panic_halt;

use litex_pac as pac;
use riscv_rt::entry;

fn uart_write(uart: &pac::Uart, value: u8) {
    while uart_txfull_read(uart) != 0 {}
    uart.rxtx().write(|w| unsafe { w.bits(value.into()) });
    uart.ev_pending().write(|w| unsafe { w.bits(0x1) });
}

fn uart_txfull_read(uart: &pac::Uart) -> u8 {
    return uart.txfull().read().bits() as u8;
}

fn hprint(uart: &pac::Uart, s: &str) {
    for c in s.bytes() {
        uart_write(uart, c);
    }
}

#[entry]
fn main() -> ! {
    let peripherals = unsafe { pac::Peripherals::steal() };
    let uart = peripherals.uart;

    loop {
        hprint(&uart, "hello\n");
    }
}
```

- `#![no_std]` and `#![no_main]`: These lines indicate that the firmware is being written without the standard library (`no_std`) and without the usual main function setup (`no_main`). This is typical for embedded systems where space and control are critical.
- `extern crate panic_halt`: This brings in the `panic_halt` crate, which simply halts the program if a panic occurs. In embedded systems, halting is often the best approach for handling errors.
- `use litex_pac as pac;`: This imports the Peripheral Access Crate (PAC) generated by LiteX. It provides access to hardware registers and interfaces.
- use `riscv_rt::entry;`: The `riscv_rt` crate provides runtime support for RISC-V.
- `fn uart_write(uart: &pac::Uart, value: u8)`: This function sends a byte over UART. It waits for the UART to be ready by checking if the transmit buffer is full (`uart_txfull_read`). Once ready, the byte is written to the UART data register, and an event pending register is cleared.
- `fn uart_txfull_read(uart: &pac::Uart) -> u8`: This function checks if the UART transmit buffer is full by reading the corresponding register.
- `fn hprint(uart: &pac::Uart, s: &str)`: This helper function prints a string (s) byte by byte over UART using `uart_write`.

There are already public Rust crates that "take care" of these interface wrappers, such as [rust-litex-hal](https://github.com/pepijndevos/rust-litex-hal).

Lets build the firmware:
```sh
cd firmware
BUILD_DIR=../build/colorlight_5a_75e cargo build --release
```

We use a different `BUILD_DIR` because the rust build script has to find the regions in order to link, generated previously by the SoC build.

My repository also contains simple cargo utilities to flash the FPGA, i.e  when running `cargo run`, cargo will try to upload the generated `.bin` via `firmware/.cargo/flash.sh`. However, if you want to simulate, you can change `config.runner` to run `firmware/.cargo/sim.sh`.

```bash
$ DEVICE=/dev/ttyUSB0 cargo run
```
*Make sure to adjust `DEVICE` to your needs, since firmware `.bin` is uploaded via UART aswell.*

Under the hood, this will run:
```bash
# create bin file
riscv64-elf-objcopy $1 -O binary $1.bin

# upload binary
litex_term --kernel $1.bin $DEVICE
```

Result:
```sh
(.venv) [roby@thonkpad firmware]$ cargo run
   Compiling litex-pac v0.1.0 (/home/roby/repos/colorlight-litex-rs/litex-pac)
   Compiling firmware v0.1.0 (/home/roby/repos/colorlight-litex-rs/firmware)
    Finished dev [unoptimized + debuginfo] target(s) in 0.53s
     Running `/home/roby/repos/colorlight-litex-rs/firmware/.cargo/sim.sh target/riscv32i-unknown-none-elf/debug/firmware`
INFO:SoC:        __   _ __      _  __  
INFO:SoC:       / /  (_) /____ | |/_/  
INFO:SoC:      / /__/ / __/ -_)>  <    
INFO:SoC:     /____/_/\__/\__/_/|_|  
INFO:SoC:  Build your hardware, easily!
INFO:SoC:--------------------------------------------------------------------------------
INFO:SoC:Creating SoC... (2024-06-13 23:29:16)
INFO:SoC:--------------------------------------------------------------------------------
INFO:SoC:FPGA device : SIM.
INFO:SoC:System clock: 1.000MHz.
INFO:SoCBusHandler:Creating Bus Handler...
INFO:SoCBusHandler:32-bit wishbone Bus, 4.0GiB Address Space.
INFO:SoCBusHandler:Adding reserved Bus Regions...
INFO:SoCBusHandler:Bus Handler created.
INFO:SoCCSRHandler:Creating CSR Handler...
INFO:SoCCSRHandler:32-bit CSR Bus, 32-bit Aligned, 16.0KiB Address Space, 2048B Paging, big Ordering (Up to 32 Locations).
INFO:SoCCSRHandler:Adding reserved CSRs...
INFO:SoCCSRHandler:CSR Handler created.
INFO:SoCIRQHandler:Creating IRQ Handler...
INFO:SoCIRQHandler:IRQ Handler (up to 32 Locations).
INFO:SoCIRQHandler:Adding reserved IRQs...
INFO:SoCIRQHandler:IRQ Handler created.

.....

hello
hello
hello
hello
hello
hello
hello
hello
hello
hello
hello
hello
```

### Conclusion

With this setup, you now have a fully integrated RISC-V system on a $15 FPGA board, all powered by open-source tools and running "safe" Rust firmware!

Next up (once I'll have some time and motivation), I'll be diving into more other topics, probably something like exploring networking capabilities or messing with the hardware to turn output ports as inputs and start implementing something bigger with this FPGA :)

### References
- [roby2014/colorlight-riscv-rs](https://github.com/roby2014/colorlight-riscv-rs)
- [Hacking a Colorlight 5A-75E board (ECP5 FPGA) with FT232RL and open-source FPGA tools.](https://roby2014-me.vercel.app/programming-a-colorlight-5a-75e-board-ECP5-FPGA-with-open-source-tools/)
- [Implementing a RISC-V soft core into a 15$ FPGA board.](https://roby2014-me.vercel.app/risc-v-colorlight-5a-75e/)
- [roby2014/risc-v-colorlight-5a-75e](https://github.com/roby2014/risc-v-colorlight-5a-75e)
- [rust-litex-hal](https://github.com/pepijndevos/rust-litex-hal)
- [rust-embedded](https://docs.rust-embedded.org/book/)