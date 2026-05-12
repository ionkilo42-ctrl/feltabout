// Debug script to check base64 encoding
import * as fs from "fs";
import * as path from "path";

const imagePath = path.resolve(process.cwd(), "../../uploads/minimax-test-image.png");

if (!fs.existsSync(imagePath)) {
  console.error("Image file not found:", imagePath);
  process.exit(1);
}

const buffer = fs.readFileSync(imagePath);
const base64 = buffer.toString("base64");

console.log("Image path:", imagePath);
console.log("File size:", buffer.length, "bytes");
console.log("Base64 length:", base64.length);
console.log("First 100 chars of base64:", base64.substring(0, 100));
console.log("Last 100 chars of base64:", base64.substring(base64.length - 100));
console.log("");
console.log("Data URL preview:", `data:image/png;base64,${base64.substring(0, 50)}...`);