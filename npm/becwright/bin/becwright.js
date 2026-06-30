#!/usr/bin/env node
"use strict";

// Thin launcher: resolves the prebuilt binary for this platform (shipped as an
// optional, os/cpu-gated dependency) and execs it. Mirrors the model used by
// esbuild, ruff and biome. No Python is involved.
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const TARGET = `${process.platform}-${process.arch}`; // e.g. linux-x64, darwin-arm64, win32-x64
const EXE = process.platform === "win32" ? "becwright.exe" : "becwright";

function resolveBinary() {
  try {
    return require.resolve(`@becwright/${TARGET}/${EXE}`);
  } catch {
    return null;
  }
}

const binary = resolveBinary();
if (!binary) {
  console.error(`becwright: no prebuilt binary for ${TARGET}.`);
  console.error("Supported: linux-x64, linux-arm64, darwin-x64, darwin-arm64, win32-x64.");
  console.error("On other platforms install via pipx: pipx install becwright");
  process.exit(1);
}

// Best effort: npm preserves the executable bit from the tarball, but restore it
// defensively in case it was lost.
if (process.platform !== "win32") {
  try {
    fs.chmodSync(binary, 0o755);
  } catch {
    /* ignore */
  }
}

// becwright's engine shells out to `becwright run <check>` for built-in checks.
// Put the binary's own directory on PATH so that subprocess resolves even when
// becwright is only a local devDependency (node_modules/.bin is not on PATH
// inside git hooks).
const env = { ...process.env };
env.PATH = path.dirname(binary) + path.delimiter + (env.PATH || "");

const result = spawnSync(binary, process.argv.slice(2), { stdio: "inherit", env });
if (result.error) {
  console.error(`becwright: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status === null ? 1 : result.status);
