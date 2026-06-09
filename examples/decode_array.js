/**
 * Decode JSON payload (b64arr / b64dtype) written by encode_array.py.
 *
 * Node: node examples/decode_array.js
 */

// Node.js: local file I/O
const fs = require("fs");
const path = require("path");
// Browser: omit fs and path; payload is obtained in main()

const DTYPE = {
  float64: Float64Array,
  int8: Int8Array,
  int16: Int16Array,
  int32: Int32Array,
};

const JSON_PATH = path.join(__dirname, "pvdata.json");

function decodeB64arr(b64arr, b64dtype) {
  const Typed = DTYPE[b64dtype];
  if (!Typed) throw new Error(`unsupported b64dtype: ${b64dtype}`);

  // Node.js: decode base64 with Buffer
  const bytes = Uint8Array.from(Buffer.from(b64arr, "base64"));
    // Browser: decode base64 with atob
    // const bytes = Uint8Array.from(atob(b64arr), (c) => c.charCodeAt(0));

  return Array.from(new Typed(bytes.buffer));
}

function main() {
  // Node.js: read pvdata.json written by encode_array.py
  if (!fs.existsSync(JSON_PATH)) {
    console.error(`missing ${JSON_PATH}`);
    console.error("run first: python examples/encode_array.py");
    process.exit(1);
  }
  const payload = JSON.parse(fs.readFileSync(JSON_PATH, "utf8"));
    // Browser: same JSON from your backend (HTTP or WebSocket)
    // const payload = await fetch("/api/pv/wfExample").then((r) => r.json());
    // const payload = JSON.parse(event.data);

  if (!payload.b64arr || !payload.b64dtype) {
    console.error("pvdata.json has no b64arr/b64dtype (was it base64-encoded?)");
    process.exit(1);
  }

  const values = decodeB64arr(payload.b64arr, payload.b64dtype);

  console.log("pvName:", payload.pvName);
  console.log("b64dtype:", payload.b64dtype);
  console.log("decoded value:", values);

  if (payload.alarm) {
    console.log("alarm:", payload.alarm);
  }
  if (payload.timeStamp) {
    console.log("timeStamp:", payload.timeStamp);
  }
}

main();
