---
layout: post
title: Fast Rust to WASM development workflow
tags: rust wasm
description: How to set up a simple and minimal workflow for developing Rust apps targetting WebAssembly and running them on the browser
---

This post describes a simple and minimal workflow for developing Rust apps targetting WASM and running them on the browser with minimal iteration time.

> See this post [on Substack!](https://danielcoelho.substack.com/p/fast-rust-wasm-workflow)

The official guides for working with Rust and WebAssembly are great ([Rust and WebAssembly](https://rustwasm.github.io/docs/book/), [The `wasm-bindgen` Guide](https://rustwasm.github.io/docs/wasm-bindgen/)), but they really railroad you into a setup where on top of Cargo you need npm, wasm-pack and webpack. You haven't even run anything yet and you have two package managers and two bundlers!

Depending on what you want to do, you can achieve the same with a lot less. Lets go through the bare minimum first, and then we'll make it slightly more ergonomic.

Note that this is roughly what Ian Kettlewell described [here](https://ianjk.com/rust-gamejam/). On that post the author mostly glanced over the setup and focused on his actual game though, but here we'll focus on the workflow side.

# The bare minimum

For the bare minimum, you'll need:
- [wasm-bindgen](https://github.com/rustwasm/wasm-bindgen);
- Run `rustup target add wasm32-unknown-unknown` once to make sure you can build to the wasm target;

Your project structure should look like this:
```
dist/
src/
    lib.rs
www/
    index.html
Cargo.toml
build.bat
```

Here's what my `Cargo.toml` looks like:
``` toml
[package]
name = "wasm_bindgen_test"
version = "0.1.0"
authors = ["Daniel Coelho"]
edition = "2018"

[lib]
crate-type = ["cdylib"]

[dependencies]
wasm-bindgen = "0.2.80"
```

Here's lib.rs:
``` Rust
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
```

And here's what `build.bat` looks like:
``` bat
@echo off

cargo build --target wasm32-unknown-unknown
wasm-bindgen --out-dir dist --target web --no-typescript target\wasm32-unknown-unknown\debug\wasm_bindgen_test.wasm
echo f | xcopy /s /f /y www\index.html dist\index.html
```

It should be pretty clear, but all that its doing is building to the wasm target, running `wasm-bindgen` to process the results and output to the `dist` folder, and copying the html file over there too.

The html file is roughly the default:
``` html
<!DOCTYPE html>
<html>

<head>
    <meta content="text/html;charset=utf-8" http-equiv="Content-Type" />
</head>

<body>
    <script type="module">
        import init,{add} from './wasm_bindgen_test.js';

        async function run() {
            await init();

            const result=add(1,2);
            console.log(`1 + 2 = ${result}`);
            if(result!==3)
                throw new Error("wasm addition doesn't work!");
        }

        run();
    </script>
</body>

</html>
```

That's pretty much it. To build you just run `build.bat`, and it will do only what you actually need, and put everything on the `dist` folder. If your rust code is including functions exported from a Javascript file, `wasm-bindgen` will actually move that file to the dist folder on its own too, which is nice! (I don't have this setup on this example for simplicity's sake).

Annoyingly you can't just double-click your html and look at the result on the browser, as it will prevent you from fetching the actual .wasm file due to CORS. There is likely a clever way around it, but realistically you're going to be doing the stuff in the next section anyway, and then it ceases to be an issue.

# Ergonomics upgrade

To make this slightly handier, we'll do what [Ian suggested](https://ianjk.com/rust-gamejam/) and setup a dev server and automatic reloading whenever we save a file.

For this part, you'll need to setup two crates:
- [cargo-watch](https://github.com/watchexec/cargo-watch) (just run `cargo install cargo-watch`);
- [devserver](https://github.com/kettle11/devserver) (just run `cargo install devserver`);

There are other alternatives if all you want is a dev server with automatic reloading (you can run a Python command, just use some vscode extensions, etc.) but I like that its just another Rust crate instead.

Once the dependencies are set up, just make a new file on your project root named `dev.bat`, and put this in there:
``` bat
START "" devserver --path dist --reload
cargo watch -d 0.05 -- build.bat
```

It should be pretty obvious: It will host the files on the `dist` folder (by default on `http://localhost:8080/` but you can change it). The second line starts `cargo watch` to observe your project and run `build.bat` 0.05 seconds after any file changes (the wait period is there as some file operations trigger multiple filesystem notices in quick succession). You can also specify glob patterns to ignore particular files or directories, but by default `cargo watch` will ignore anything on your .gitignore, which tends to work pretty well.

Also note that the first command is run with `START` to run it on a separate command prompt (as it will block it while it runs) that you can mostly put away. The second command will run on your current terminal, which is good because that's where your `cargo build` output (compile errors and so on) will end up, which you likely want to keep an eye on.

That should be it! When you want to start working, just run `dev.bat` on your terminal and open `http://localhost:8080/` on a browser. On my machine it takes about a second to go from hitting `Ctrl+S` to save some file and seeing the updated page (the first couple of reloads will be a bit slower than usual of course). Even on larger projects it has never surpassed a few seconds for me.

Let me know if you know how to simplify or make this even faster!