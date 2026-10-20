import test from "node:test";
import assert from "node:assert/strict";
import { add } from "../dist/index.js";

test("add returns the sum", () => {
  assert.equal(add(2, 2), 4);
});
