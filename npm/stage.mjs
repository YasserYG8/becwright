// Copies a freshly built PyInstaller binary into its platform package so it can
// be published to npm. Used by CI (one call per built target) and for local
// testing.
//   node npm/stage.mjs <target> <binaryPath>
// e.g. node npm/stage.mjs linux-x64 dist/becwright
import { copyFileSync, chmodSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const [target, binaryPath] = process.argv.slice(2);
if (!target || !binaryPath) {
  console.error("usage: node npm/stage.mjs <target> <binaryPath>");
  process.exit(1);
}

const here = dirname(fileURLToPath(import.meta.url));
const isWin = target.startsWith("win32");
const dest = join(here, "platforms", target, isWin ? "becwright.exe" : "becwright");

copyFileSync(binaryPath, dest);
if (!isWin) chmodSync(dest, 0o755);
console.log(`staged ${binaryPath} -> ${dest}`);
