[![smithery badge](https://smithery.ai/badge/@jifrozen0110/riot)](https://smithery.ai/server/@jifrozen0110/riot)
# MCP Riot Server

**MCP-Riot is a community-developed [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) server that integrates with the Riot Games API** to provide League of Legends data to AI assistants via natural language queries.

This project enables AI models to retrieve player information, ranked stats, champion mastery, and recent match summaries.

> **Disclaimer:** This is an open-source project *not affiliated with or endorsed by Riot Games.* League of Legends® is a registered trademark of Riot Games, Inc.

---
## Demo
![mcp-riot-lol](https://github.com/user-attachments/assets/ef0c62d7-f99b-4a74-bc7d-8b737bf8fe2a)


## ✨ Features

### 🧾 Player Summary
> "What's the current rank and top champions of Hide on bush?"

Provides the player's:
- Level
- Ranked Solo Tier
- Top champion masteries
- Recent match history

### 🔝 Top Champions
> "What champions is he best at?"

Returns the top N champions based on mastery points.

### 🎯 Champion Mastery
> "How good is this player with Ahri?"

Returns detailed champion mastery data for a specific champion.

### 🕹️ Recent Matches
> "Show the last 3 matches for this summoner"

Lists recent matches including champion used, K/D/A, and result.

### 📊 Match Summary
> "Summarize this match for a given match ID"

Returns the player’s match stats, such as KDA, damage, wards, and result.

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/jifrozen0110/mcp-riot.git
cd mcp-riot

# Install dependencies (using uv or pip)
uv sync
```


### 2. Get Your API Key and Set Environment

Create `.env` file with your Riot API key:

```ini
RIOT_API_KEY=your_riot_api_key
```
You can get your key from https://developer.riotgames.com/


### 3. Configure MCP Client

Register this server in your MCP client (e.g., Claude for Desktop).

Edit ~/Library/Application Support/Claude/claude_desktop_config.json:

``` bash
{
    "mcpServers": {
        "amadeus": {
            "command": "/ABSOLUTE/PATH/TO/PARENT/FOLDER/uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER",
                "run",
                "--env-file",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/.env",
                "riot.py"
            ]
        }
    }
}
```

> Replace `/ABSOLUTE/PATH/TO/PARENT/FOLDER/` with the actual path to your project folder.

my case:

``` bash
{
    "mcpServers": {
        "amadeus": {
            "command": "/Users/jifrozen/.local/bin/uv",
            "args": [
                "--directory",
                "/Users/jifrozen/mcp-riot/src/",
                "run",
                "--env-file",
                "/Users/jifrozen/mcp-riot/.env",
                "server.py"
            ]
        }
    }
}

```

---
## 🛠️ Tools

The following tools will be exposed to MCP clients:

### `get_player_summary`

Summarizes level, rank, top champions, and recent matches.

### `get_top_champions_tool`

Returns top champions by mastery points.

### `get_champion_mastery_tool`

Returns mastery details for a specific champion.

### `get_recent_matches_tool`

Returns recent matches for the given summoner.

### `get_match_summary`

Returns match performance stats for a given match ID and puuid.

---

## 📚 References

- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Riot Games API Docs](https://developer.riotgames.com/)
- [Data Dragon (static data)](https://developer.riotgames.com/docs/lol#data-dragon)

---

## 📝 License

MIT License © 2025 [jifrozen0110](https://github.com/jifrozen0110)
