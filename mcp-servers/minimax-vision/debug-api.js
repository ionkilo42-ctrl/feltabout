// Debug script to test API directly
import OpenAI from "openai";
import * as fs from "fs";
import * as path from "path";

const imagePath = path.resolve(process.cwd(), "../../uploads/minimax-test-image.png");

if (!fs.existsSync(imagePath)) {
  console.error("Image file not found:", imagePath);
  process.exit(1);
}

const buffer = fs.readFileSync(imagePath);
const base64 = buffer.toString("base64");

const apiKey = process.env.MINIMAX_API_KEY;
const baseUrl = process.env.MINIMAX_BASE_URL || "https://api.minimax.io/v1";
const model = process.env.MINIMAX_MODEL || "MiniMax-M2.7";

console.log("API Key set:", !!apiKey);
console.log("Base URL:", baseUrl);
console.log("Model:", model);
console.log("Image size:", buffer.length, "bytes");
console.log("");

const client = new OpenAI({ apiKey, baseURL: baseUrl });

// Try with a simple prompt first
const simplePrompt = "Describe this image briefly.";

console.log("Sending request to MiniMax API...");

try {
  const response = await client.chat.completions.create({
    model: model,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: simplePrompt,
          },
          {
            type: "image_url",
            image_url: {
              url: `data:image/png;base64,${base64}`,
            },
          },
        ],
      },
    ],
    max_tokens: 500,
  });

  console.log("\n=== RESPONSE ===");
  console.log("Content:", response.choices[0]?.message?.content);
  console.log("Model:", response.model);
  console.log("Usage:", JSON.stringify(response.usage, null, 2));
} catch (error) {
  console.error("\n=== ERROR ===");
  console.error("Error message:", error.message);
  if (error.response) {
    console.error("Response status:", error.response.status);
    console.error("Response body:", JSON.stringify(error.response.data, null, 2));
  }
}