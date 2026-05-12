// Quick test script to analyze image using URL
import { analyzeImageWithMinimax } from "./dist/utils/minimax_client.js";

const imageUrl = "https://minimax-algeng-chat-tts-us.oss-us-east-1.aliyuncs.com/ccv2%2F2026-05-12%2FMiniMax-M2.7%2F2022011110487495515%2F98ae440271b450a5a3fcaa71957e088652548da1a9bc9fed0681c00cbe9ff172..png?Expires=1778640610&OSSAccessKeyId=LTAI5tCpJNKCf5EkQHSuL9xg&Signature=KsJpka8If7R9hkdHaKJv1rrPl4Q%3D";

console.log("Analyzing image from URL...\n");

try {
  const result = await analyzeImageWithMinimax({
    imagePath: imageUrl,
  });
  console.log("Analysis Result:");
  console.log("================");
  console.log(result);
} catch (error) {
  console.error("Error:", error.message);
}
