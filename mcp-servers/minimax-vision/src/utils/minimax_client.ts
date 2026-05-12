import OpenAI from "openai";
import * as fs from "fs";
import * as path from "path";

export interface VisionAnalysisResult {
  visible_ui_elements: string[];
  text_found: string[];
  layout_issues: string[];
  likely_bugs: string[];
  suggested_fixes: string[];
}

export interface AnalyzeImageOptions {
  imagePath: string;
  prompt?: string;
}

function getConfig(): { apiKey: string; baseUrl: string; model: string } {
  const apiKey = process.env.MINIMAX_API_KEY;
  if (!apiKey) {
    throw new Error("MINIMAX_API_KEY environment variable is not set");
  }

  const baseUrl = process.env.MINIMAX_BASE_URL || "https://api.minimax.io/v1";
  const model = process.env.MINIMAX_MODEL || "MiniMax-VL-01";

  return { apiKey, baseUrl, model };
}

function readImageAsBase64(imagePath: string): string {
  const absolutePath = path.isAbsolute(imagePath)
    ? imagePath
    : path.resolve(process.cwd(), imagePath);

  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Image file not found: ${absolutePath}`);
  }

  const buffer = fs.readFileSync(absolutePath);
  return buffer.toString("base64");
}

function getMimeType(imagePath: string): string {
  const ext = path.extname(imagePath).toLowerCase();
  const mimeTypes: Record<string, string> = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
  };
  return mimeTypes[ext] || "image/jpeg";
}

const DEFAULT_ANALYSIS_PROMPT = `You are a precise coding assistant analyzing a screenshot or image.

Provide a concise analysis with these sections:

1. **Visible UI Elements**: List the key UI components visible (buttons, forms, navigation, etc.)

2. **Text/OCR Found**: Extract all readable text, code, or content visible in the image

3. **Layout Issues**: Note any layout problems like:
   - Overlapping elements
   - Misalignment
   - Overflow/clipping issues
   - Missing spacing or gaps
   - Broken responsive behavior

4. **Likely Frontend Bugs**: Identify potential bugs such as:
   - Missing or broken styles
   - Incorrect states (hover, focus, disabled)
   - Broken interactivity
   - Console errors or warnings
   - Accessibility violations

5. **Suggested Fixes**: Provide concrete, actionable fixes for any issues found

Be specific and technical. Focus on practical debugging information.`;

export async function analyzeImageWithMinimax(
  options: AnalyzeImageOptions
): Promise<string> {
  const { apiKey, baseUrl, model } = getConfig();
  const { imagePath, prompt } = options;

  const client = new OpenAI({ apiKey, baseURL: baseUrl });

  const base64Image = readImageAsBase64(imagePath);
  const mimeType = getMimeType(imagePath);
  const analysisPrompt = prompt || DEFAULT_ANALYSIS_PROMPT;

  try {
    const response = await client.chat.completions.create({
      model,
      messages: [
        {
          role: "user",
          content: [
            {
              type: "text",
              text: analysisPrompt,
            },
            {
              type: "image_url",
              image_url: {
                url: `data:${mimeType};base64,${base64Image}`,
                detail: "high",
              },
            },
          ],
        },
      ],
      max_tokens: 2000,
      temperature: 0.3,
    });

    const result = response.choices[0]?.message?.content;
    if (!result) {
      throw new Error("Empty response from MiniMax API");
    }

    return result;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`MiniMax API error: ${error.message}`);
    }
    throw error;
  }
}
