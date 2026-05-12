import { Tool } from "@modelcontextprotocol/sdk/types.js";
import { analyzeImageWithMinimax } from "../utils/minimax_client.js";

export const ANALLYZE_IMAGE_TOOL_NAME = "analyze_image";

export interface AnalyzeImageArguments {
  image_path: string;
  prompt?: string;
}

export const analyzeImageTool: Tool = {
  name: ANALLYZE_IMAGE_TOOL_NAME,
  description: `Analyze an image screenshot to identify visible UI elements, text, layout issues, likely bugs, and suggested fixes.

This tool is useful for:
- Debugging frontend issues from screenshots
- Understanding UI layout and structure
- Identifying visual bugs or rendering issues
- Extracting text/OCR from images
- Reviewing UI designs

Arguments:
- image_path: Path or URL to the image file (absolute file path, relative path, or https:// URL)
- prompt: Optional custom prompt to guide the analysis`,
  inputSchema: {
    type: "object",
    properties: {
      image_path: {
        type: "string",
        description: "Path or URL to the image file to analyze (file path or https:// URL)",
      },
      prompt: {
        type: "string",
        description: "Optional custom prompt to guide the analysis",
      },
    },
    required: ["image_path"],
  },
};

export async function handleAnalyzeImage(
  args: AnalyzeImageArguments
): Promise<{ content: Array<{ type: "text"; text: string }> }> {
  try {
    const result = await analyzeImageWithMinimax({
      imagePath: args.image_path,
      prompt: args.prompt,
    });

    return {
      content: [
        {
          type: "text",
          text: result,
        },
      ],
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error occurred";
    return {
      content: [
        {
          type: "text",
          text: `Error analyzing image: ${errorMessage}`,
        },
      ],
    };
  }
}
