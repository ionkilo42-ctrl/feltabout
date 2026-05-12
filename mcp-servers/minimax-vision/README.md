# MiniMax Vision MCP Server

A Model Context Protocol (MCP) server that enables Cline to analyze images using MiniMax Vision models.

## Features

- **analyze_image tool**: Analyze screenshots/images to identify UI elements, extract text, detect layout issues, and suggest bug fixes
- Uses MiniMax VL models via OpenAI-compatible API
- API key stored in environment variable (never hardcoded)

## Prerequisites

- Node.js 18+ 
- A MiniMax API key (get one at https://platform.minimax.io)

## Installation

1. Navigate to the server directory:
   ```bash
   cd mcp-servers/minimax-vision
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

4. Add your MiniMax API key to `.env`:
   ```
   MINIMAX_API_KEY=sk-cp-your-actual-api-key
   ```

5. Build the TypeScript:
   ```bash
   npm run build
   ```

## Cline MCP Configuration

Add this to your Cline MCP settings (`~/.clinerules/settings.json` or via VS Code settings):

```json
{
  "mcpServers": {
    "minimax-vision-mcp": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/path/to/Feltabout/mcp-servers/minimax-vision",
      "env": {
        "MINIMAX_API_KEY": "sk-cp-your-api-key-here"
      }
    }
  }
}
```

**Note**: Replace `/path/to/Feltabout` with your actual Feltabout directory path.

## Usage

Once configured in Cline, use the `analyze_image` tool:

```
analyze_image with:
{
  "image_path": "/path/to/screenshot.png",
  "prompt": "Focus on finding CSS grid issues"  // optional
}
```

### Example

```json
{
  "image_path": "./frontend/public/screenshot.png"
}
```

## Output Format

The analysis includes:

1. **Visible UI Elements** - Key components visible (buttons, forms, navigation, etc.)
2. **Text/OCR Found** - All readable text and content
3. **Layout Issues** - Overlapping elements, misalignment, overflow issues
4. **Likely Frontend Bugs** - Missing styles, broken states, accessibility violations
5. **Suggested Fixes** - Concrete, actionable fixes

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MINIMAX_API_KEY` | Yes | - | Your MiniMax API key |
| `MINIMAX_BASE_URL` | No | `https://api.minimax.io/v1` | API endpoint |
| `MINIMAX_MODEL` | No | `MiniMax-VL-01` | Vision model to use |

## Troubleshooting

**"MINIMAX_API_KEY environment variable is not set"**
- Make sure you've added the API key to your `.env` file
- Or set it directly in your Cline MCP config's `env` section

**"Image file not found"**
- Use absolute paths or ensure relative paths are relative to the working directory
- Check that the file exists and is readable

**Build errors**
- Ensure Node.js 18+ is installed
- Run `npm install` again to ensure all dependencies are present
