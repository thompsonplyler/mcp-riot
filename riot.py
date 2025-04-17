from mcp.server.fastmcp import FastMCP
import httpx
import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("riot")

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
if not RIOT_API_KEY:
    raise EnvironmentError("RIOT_API_KEY is not set in the environment variables.")

CHAMPION_MAP: dict[str, dict[int, str]] = {}  # language -> {champ_id: name}


async def riot_request(
    url: str, region: str = "kr", params: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    headers = {
        "X-Riot-Token": RIOT_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            full_url = f"https://{region}.api.riotgames.com{url}"
            res = await client.get(full_url, headers=headers, params=params, timeout=30.0)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Riot API Error: {e}")
            return None


async def get_champion_map(language: str = "ko_KR") -> dict[int, str]:
    if language in CHAMPION_MAP:
        return CHAMPION_MAP[language]

    async with httpx.AsyncClient() as client:
        version_res = await client.get("https://ddragon.leagueoflegends.com/api/versions.json")
        version = version_res.json()[0]
        champ_res = await client.get(
            f"https://ddragon.leagueoflegends.com/cdn/{version}/data/{language}/champion.json"
        )
        data = champ_res.json()["data"]
        CHAMPION_MAP[language] = {int(c["key"]): c["name"] for c in data.values()}
        return CHAMPION_MAP[language]


async def get_puuid(game_name: str, tag_line: str) -> str | None:
    url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {
        "X-Riot-Token": RIOT_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            res.raise_for_status()
            return res.json()["puuid"]
    except Exception:
        return None


async def get_summoner_by_puuid(puuid: str) -> dict[str, Any] | None:
    return await riot_request(f"/lol/summoner/v4/summoners/by-puuid/{puuid}")


async def get_rank_by_summoner_id(summoner_id: str) -> str:
    rank_data = await riot_request(f"/lol/league/v4/entries/by-summoner/{summoner_id}")
    if not rank_data:
        return "No ranked data available."

    solo = next((q for q in rank_data if q["queueType"] == "RANKED_SOLO_5x5"), None)
    if solo:
        tier, rank = solo["tier"], solo["rank"]
        lp, wins, losses = solo["leaguePoints"], solo["wins"], solo["losses"]
        winrate = round(wins / (wins + losses) * 100)
        return f"{tier} {rank} ({lp} LP) - {wins}W {losses}L ({winrate}% WR)"
    return "Unranked in Solo Queue."


async def get_top_champions(puuid: str, champ_map: dict[int, str], count: int = 3) -> str:
    mastery_data = await riot_request(
        f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top", params={"count": count}
    )
    if not mastery_data:
        return "No champion mastery data found."

    return "\n".join(
        f"- {champ_map.get(c['championId'], f'ID({c['championId']})')}: Level {c['championLevel']}, {c['championPoints']} pts"
        for c in mastery_data
    )


@mcp.tool()
async def get_top_champions_tool(game_name: str, tag_line: str, language: str = "en_US", count: int = 3) -> str:
    """
    🔝 Get the player's top champion masteries.

    Returns a list of the player's most-played champions based on mastery points.
    """
    puuid = await get_puuid(game_name, tag_line)
    if not puuid:
        return "Failed to find player."

    champ_map = await get_champion_map(language)
    return await get_top_champions(puuid, champ_map, count)


async def get_recent_matches(puuid: str, count: int = 3) -> str:
    match_ids = await riot_request(
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids", region="asia", params={"count": count}
    )
    if not match_ids:
        return "No recent matches found."

    matches = []
    for match_id in match_ids:
        match = await riot_request(f"/lol/match/v5/matches/{match_id}", region="asia")
        if match:
            participant = next((p for p in match["info"]["participants"] if p["puuid"] == puuid), None)
            if participant:
                champ = participant["championName"]
                k, d, a = participant["kills"], participant["deaths"], participant["assists"]
                result = "Win" if participant["win"] else "Loss"
                matches.append(f"{match_id} {champ}: {k}/{d}/{a} - {result}")
    return "\n".join(matches)


@mcp.tool()
async def get_recent_matches_tool(game_name: str, tag_line: str, count: int = 3) -> str:
    """
    🕹️ Get the player's recent match history.

    Returns a brief summary of the player's most recent matches, including champion, score, and result.
    """
    puuid = await get_puuid(game_name, tag_line)
    if not puuid:
        return "Failed to find player."
    return await get_recent_matches(puuid, count)



@mcp.tool()
async def get_champion_mastery_tool(game_name: str, tag_line: str, champion_name: str, language: str = "en_US") -> dict[str, Any] | str:
    """
    🎯 Get the player's mastery info for a specific champion.

    Returns detailed mastery data (level, points, last play time, etc.) for the requested champion.
    """
    puuid = await get_puuid(game_name, tag_line)
    if not puuid:
        return "Failed to find player."

    champion_map = await get_champion_map(language)
    champion_id = next((cid for cid, name in champion_map.items() if name.lower() == champion_name.lower()), None)
    if not champion_id:
        return f"Champion '{champion_name}' not found."

    mastery = await riot_request(
        f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/by-champion/{champion_id}"
    )
    if not mastery:
        return f"Could not find mastery data for {champion_name}."

    return {
        "game_name": game_name,
        "tag_line": tag_line,
        "puuid": puuid,
        "champion_name": champion_name,
        "champion_id": champion_id,
        "champion_mastery": mastery
    }


@mcp.tool()
async def get_player_summary(game_name: str, tag_line: str, language: str = "en_US") -> str:
    """
    🧾 Get a complete summary of a player's profile.

    Includes level, solo rank, top champion masteries, and recent matches in a single output.
    """
    puuid = await get_puuid(game_name, tag_line)
    if not puuid:
        return "Failed to find player."

    champ_map = await get_champion_map(language)
    summoner = await get_summoner_by_puuid(puuid)
    if not summoner:
        return "Failed to get summoner profile."

    level = summoner["summonerLevel"]
    rank = await get_rank_by_summoner_id(summoner["id"])
    top_champs = await get_top_champions(puuid, champ_map, count=3)
    matches = await get_recent_matches(puuid)

    return f"""
👤 {game_name} (Level {level})

🏅 Rank: {rank}

🔥 Top Champions:
{top_champs}

🕹️ Recent Matches:
{matches}
"""

@mcp.tool()
async def get_match_summary(match_id: str, puuid: str) -> dict[str, Any] | str:
    """
    📊 Get a detailed summary of a specific match for a given player.

    Extracts and returns only the relevant stats (KDA, damage, vision, win/loss, etc.) from the match.
    """
    match = await riot_request(f"/lol/match/v5/matches/{match_id}", region="asia")
    if not match:
        return "Failed to load match data."

    participant = next((p for p in match["info"]["participants"] if p["puuid"] == puuid), None)
    if not participant:
        return f"No participant found with puuid: {puuid}"

    return {
        "championName": participant["championName"],
        "lane": participant["lane"],
        "role": participant["role"],
        "kills": participant["kills"],
        "deaths": participant["deaths"],
        "assists": participant["assists"],
        "kda": participant["challenges"].get("kda"),
        "killParticipation": participant["challenges"].get("killParticipation"),
        "totalDamageDealtToChampions": participant["totalDamageDealtToChampions"],
        "visionScore": participant["visionScore"],
        "wardsPlaced": participant["wardsPlaced"],
        "wardsKilled": participant["wardsKilled"],
        "win": participant["win"],
        "teamPosition": participant.get("teamPosition"),
        "timePlayed": participant["timePlayed"],
        "gameDuration": match["info"]["gameDuration"],
        "queueId": match["info"]["queueId"],
    }


if __name__ == "__main__":
    # Initialize and run the server
    # import asyncio
    # asyncio.run(load_champion_data())
    # mcp.run(transport='stdio')
    # print(get_summoner_id("지언이랑신길에서","174"))
    import asyncio

    async def test():
        print("🔍 get_top_mastery 테스트 중...")
        result = await get_champion_mastery_tool("지언이랑신길에서","174","아트록스","ko_KR")
        print("결과:", result)

    asyncio.run(test())
