// Debug script to test different image formats
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

const simplePrompt = "Describe this image briefly.";

// Try format 1: image_url as string (simplest approach)
console.log("\n=== TEST 1: image_url as simple string ===");

try {
  const response1 = await client.chat.completions.create({
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
            image_url: `data:image/png;base64,${base64}`,
          },
        ],
      },
    ],
    max_tokens: 500,
  });

  console.log("Response:", response1.choices[0]?.message?.content);
  console.log("Prompt tokens:", response1.usage?.prompt_tokens);
} catch (error) {
  console.error("Error:", error.message);
}

// Try format 2: multiple content items as separate messages
console.log("\n=== TEST 2: Image in separate content item ===");

try {
  const response2 = await client.chat.completions.create({
    model: model,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: simplePrompt,
          },
        ],
      },
      {
        role: "user",
        content: [
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

  console.log("Response:", response2.choices[0]?.message?.content);
  console.log("Prompt tokens:", response2.usage?.prompt_tokens);
} catch (error) {
  console.error("Error:", error.message);
}

// Try format 3: URL image (not base64)
console.log("\n=== TEST 3: URL-based image (just text) ===");

try {
  const response3 = await client.chat.completions.create({
    model: model,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: "What do you see? (testing without image)",
          },
        ],
      },
    ],
    max_tokens: 500,
  });

  console.log("Response:", response3.choices[0]?.message?.content);
  console.log("Prompt tokens:", response3.usage?.prompt_tokens);
} catch (error) {
  console.error("Error:", error.message);
}