# Setting Up GTA in Claude Desktop

This guide walks you through connecting Claude Desktop to the Global Trade Alert database. Once set up, you can ask Claude questions about trade policy — tariffs, subsidies, export bans, and more — and get answers backed by real data from 200+ countries.

No programming knowledge required. The whole process takes about 10 minutes.

---

## Step 1: Install a small helper tool

Claude Desktop needs a tool called **uv** to run the GTA connection. Think of it as a one-time setup step — like installing a printer driver.

### On a Mac

1. Open **Terminal** (press `Cmd + Space`, type "Terminal", press Enter)
2. Paste this line and press Enter:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. You'll see some installation text. When it finishes, **close Terminal completely** and reopen it.
4. Type `uvx --version` and press Enter. You should see a version number like `0.6.x`. If you do, you're good.

### On Windows

1. Open **PowerShell** (press `Win + X`, select "Windows PowerShell")
2. Paste this line and press Enter:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Close PowerShell and reopen it.
4. Type `uvx --version` and press Enter. You should see a version number.

---

## Step 2: Get your GTA API key

You need a key that lets Claude access the GTA database.

1. Go to https://globaltradealert.org/api-access
2. You will receive a demo API key directly. For full access, request credentials from the support team.
3. Copy your API key somewhere safe — you'll need it in the next step.

Your key will look something like: `abc123def456...`

---

## Step 3: Tell Claude Desktop about GTA

You need to edit a small settings file. This is the trickiest step, but just follow along carefully.

### On a Mac

1. Open **Finder**
2. In the menu bar, click **Go** → **Go to Folder...**
3. Paste this path and press Enter:

```
~/Library/Application Support/Claude
```

4. Look for a file called `claude_desktop_config.json`
   - **If it exists:** Open it with TextEdit (right-click → Open With → TextEdit)
   - **If it doesn't exist:** Open TextEdit, create a new blank file, and save it in this folder with the name `claude_desktop_config.json`

5. The file should contain exactly this (replace `your-api-key-here` with the key from Step 2):

```json
{
  "mcpServers": {
    "gta": {
      "command": "uvx",
      "args": ["sgept-gta-mcp@latest"],
      "env": {
        "GTA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

> **Already have other MCP servers?** If your file already has content, add the `"gta": { ... }` block inside the existing `"mcpServers"` section, separated by a comma. If you're not sure how, ask Claude to help you edit the JSON.

6. Save and close the file.

### On Windows

1. Press `Win + R`, paste this path, and press Enter:

```
%APPDATA%\Claude
```

2. Follow the same process as Mac (steps 4-6), opening or creating `claude_desktop_config.json`.

---

## Step 4: Restart Claude Desktop

This is important — you must **fully quit** Claude Desktop, not just close the window.

- **Mac:** Click the Claude icon in your menu bar (top right of screen) → Quit. Then reopen Claude Desktop.
- **Windows:** Right-click the Claude icon in your system tray (bottom right) → Quit. Then reopen.

---

## Step 5: Test it

Open a new conversation in Claude Desktop and type:

> Show me 3 recent trade interventions implemented by the United States.

If everything is working, Claude will show you a formatted list of US trade measures with titles, dates, and links to the GTA website.

---

## Troubleshooting

**Claude doesn't seem to know about GTA / "tool not found"**
- Did you fully quit and restart Claude Desktop (not just close the window)?
- Is your `claude_desktop_config.json` valid? Common mistakes:
  - Missing or extra commas
  - Mismatched quotes or brackets
  - The file was saved as `.json.txt` instead of `.json`
- Try pasting your config file into Claude and asking "Is this valid JSON?"

**"uvx: command not found" or similar error**
- Go back to Step 1 and make sure uv installed correctly.
- Did you close and reopen your terminal after installing?
- Try running `uvx --version` in a fresh terminal window.

**"Authentication Error"**
- Double-check your API key in the config file — no extra spaces or missing characters.
- Make sure you replaced `your-api-key-here` with your actual key.
- Verify your key at https://globaltradealert.org/api-access.

**Still stuck?**
- Contact support@sgept.org with a description of what you see.
