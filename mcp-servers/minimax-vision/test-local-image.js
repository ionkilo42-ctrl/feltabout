// Test script to analyze local image
// Uses --env-file flag to load .env automatically
import { analyzeImageWithMinimax } from "./dist/utils/minimax_client.js";
import * as fs from "fs";
import * as path from "path";

const imagePath = path.resolve(process.cwd(), "../../uploads/minimax-test-image.png");

// Confirm file exists
if (!fs.existsSync(imagePath)) {
  console.error("Error: Image file not found:", imagePath);
  process.exit(1);
}

const stats = fs.statSync(imagePath);
console.log("Image file found:", imagePath);
console.log("File size:", stats.size, "bytes");
console.log("API Key set:", !!process.env.MINIMAX_API_KEY);
console.log("Model:", process.env.MINIMAX_MODEL || "MiniMax-M2.7 (default)");
console.log("");

try {
  const result = await analyzeImageWithMinimax({
    imagePath: imagePath,
  });
  console.log("\n=== IMAGE ANALYSIS RESULT ===\n");
  console.log(result);
  console.log("\n=== END OF RESULT ===");
} catch (error) {
  console.error("Error:", error.message);
  process.exit(1);
}