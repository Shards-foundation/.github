import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

function walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) {
      walk(path);
      continue;
    }
    if (!path.endsWith(".ts")) {
      continue;
    }
    const text = readFileSync(path, "utf8");
    if (text.includes("debugger")) {
      console.error(`${path}: debugger statements are not allowed`);
      process.exitCode = 1;
    }
  }
}

walk("src");
if (process.exitCode) {
  process.exit(process.exitCode);
}
console.log("lint ok");
