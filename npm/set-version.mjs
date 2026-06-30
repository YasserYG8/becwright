// Sets the version across the launcher and every platform package, and keeps the
// launcher's optionalDependencies in sync. Run by CI from the release tag.
//   node npm/set-version.mjs <version>   (e.g. 0.1.0)
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const version = process.argv[2];
if (!version || !/^\d+\.\d+\.\d+/.test(version)) {
  console.error("usage: node npm/set-version.mjs <version>  (e.g. 0.1.0)");
  process.exit(1);
}

const here = dirname(fileURLToPath(import.meta.url));

function patch(file, fn) {
  const pkg = JSON.parse(readFileSync(file, "utf8"));
  fn(pkg);
  writeFileSync(file, JSON.stringify(pkg, null, 2) + "\n");
  console.log(`set ${pkg.name} -> ${version}`);
}

patch(join(here, "becwright", "package.json"), (pkg) => {
  pkg.version = version;
  for (const dep of Object.keys(pkg.optionalDependencies || {})) {
    pkg.optionalDependencies[dep] = version;
  }
});

const platforms = join(here, "platforms");
for (const target of readdirSync(platforms)) {
  patch(join(platforms, target, "package.json"), (pkg) => {
    pkg.version = version;
  });
}
