// Reads JSON from stdin, writes TOON (official @toon-format/toon encoder) to stdout.
import { encode } from "@toon-format/toon";
let buf = "";
process.stdin.on("data", (d) => (buf += d));
process.stdin.on("end", () => process.stdout.write(encode(JSON.parse(buf))));
