#!/usr/bin/env python3
"""
Generate realistic player stats based on position and IoG for Galactico11.
"""
import json
import re
from pathlib import Path

def get_position_roles(positions):
    """Determine player roles from positions."""
    roles = {
        'is_gk': any(p == 'GK' for p in positions),
        'is_defender': any(p in ['CB', 'LB', 'RB', 'LWB', 'RWB'] for p in positions),
        'is_midfielder': any(p in ['CDM', 'CM', 'CAM'] for p in positions),
        'is_winger': any(p in ['LW', 'RW', 'LM', 'RM'] for p in positions),
        'is_forward': any(p in ['ST', 'CF'] for p in positions),
    }
    return roles

def generate_stats(player_name, positions, iog):
    """Generate realistic stats based on position and IoG."""
    roles = get_position_roles(positions)
    
    # Normalize IoG to 0-1 scale (typical IoG ranges from 80-99)
    iog_factor = (iog - 80) / 20 if iog >= 80 else 0.1
    iog_factor = max(0.0, min(1.0, iog_factor))
    
    stats = {}
    
    # Goalkeeper
    if roles['is_gk']:
        stats['goals'] = 0
        stats['assists'] = 0
        stats['xG'] = 0
        stats['xA'] = 0
        stats['tackles'] = round(5 + iog_factor * 15)
        stats['interceptions'] = round(20 + iog_factor * 60)
        stats['progressivePasses'] = round(200 + iog_factor * 400)
        stats['progressiveCarries'] = round(5 + iog_factor * 15)
        stats['keyPasses'] = round(2 + iog_factor * 8)
    
    # Pure Defender (CB, LB, RB)
    elif roles['is_defender'] and not roles['is_midfielder'] and not roles['is_winger']:
        stats['goals'] = round(iog_factor * 3)
        stats['assists'] = round(iog_factor * 2)
        stats['xG'] = round(iog_factor * 0.5)
        stats['xA'] = round(iog_factor * 0.8)
        stats['tackles'] = round(100 + iog_factor * 150)
        stats['interceptions'] = round(50 + iog_factor * 100)
        stats['progressivePasses'] = round(300 + iog_factor * 400)
        stats['progressiveCarries'] = round(30 + iog_factor * 70)
        stats['keyPasses'] = round(10 + iog_factor * 20)
    
    # Midfielder
    elif roles['is_midfielder'] and not roles['is_forward']:
        if 'CAM' in positions:
            # Attacking Midfielder
            stats['goals'] = round(3 + iog_factor * 12)
            stats['assists'] = round(2 + iog_factor * 10)
            stats['xG'] = round(1 + iog_factor * 4)
            stats['xA'] = round(2 + iog_factor * 6)
            stats['tackles'] = round(30 + iog_factor * 60)
            stats['interceptions'] = round(20 + iog_factor * 50)
            stats['progressivePasses'] = round(200 + iog_factor * 350)
            stats['progressiveCarries'] = round(100 + iog_factor * 200)
            stats['keyPasses'] = round(30 + iog_factor * 80)
        elif 'CDM' in positions:
            # Defensive Midfielder
            stats['goals'] = round(1 + iog_factor * 5)
            stats['assists'] = round(1 + iog_factor * 3)
            stats['xG'] = round(0.2 + iog_factor * 1)
            stats['xA'] = round(0.5 + iog_factor * 2)
            stats['tackles'] = round(80 + iog_factor * 120)
            stats['interceptions'] = round(60 + iog_factor * 100)
            stats['progressivePasses'] = round(250 + iog_factor * 400)
            stats['progressiveCarries'] = round(40 + iog_factor * 100)
            stats['keyPasses'] = round(15 + iog_factor * 40)
        else:
            # Box-to-Box Midfielder
            stats['goals'] = round(2 + iog_factor * 8)
            stats['assists'] = round(1 + iog_factor * 6)
            stats['xG'] = round(0.5 + iog_factor * 3)
            stats['xA'] = round(1 + iog_factor * 4)
            stats['tackles'] = round(50 + iog_factor * 80)
            stats['interceptions'] = round(40 + iog_factor * 70)
            stats['progressivePasses'] = round(220 + iog_factor * 380)
            stats['progressiveCarries'] = round(70 + iog_factor * 150)
            stats['keyPasses'] = round(20 + iog_factor * 60)
    
    # Winger
    elif roles['is_winger'] and not roles['is_forward']:
        stats['goals'] = round(5 + iog_factor * 15)
        stats['assists'] = round(3 + iog_factor * 12)
        stats['xG'] = round(2 + iog_factor * 8)
        stats['xA'] = round(2 + iog_factor * 8)
        stats['tackles'] = round(20 + iog_factor * 40)
        stats['interceptions'] = round(15 + iog_factor * 35)
        stats['progressivePasses'] = round(150 + iog_factor * 300)
        stats['progressiveCarries'] = round(150 + iog_factor * 250)
        stats['keyPasses'] = round(25 + iog_factor * 70)
    
    # Forward / Striker
    elif roles['is_forward']:
        stats['goals'] = round(8 + iog_factor * 32)
        stats['assists'] = round(1 + iog_factor * 8)
        stats['xG'] = round(3 + iog_factor * 12)
        stats['xA'] = round(1 + iog_factor * 5)
        stats['tackles'] = round(10 + iog_factor * 20)
        stats['interceptions'] = round(5 + iog_factor * 15)
        stats['progressivePasses'] = round(100 + iog_factor * 200)
        stats['progressiveCarries'] = round(100 + iog_factor * 200)
        stats['keyPasses'] = round(10 + iog_factor * 40)
    
    # Default fallback
    else:
        stats['goals'] = round(2 + iog_factor * 5)
        stats['assists'] = round(1 + iog_factor * 3)
        stats['xG'] = round(0.5 + iog_factor * 2)
        stats['xA'] = round(0.5 + iog_factor * 2)
        stats['tackles'] = round(30 + iog_factor * 50)
        stats['interceptions'] = round(20 + iog_factor * 40)
        stats['progressivePasses'] = round(150 + iog_factor * 300)
        stats['progressiveCarries'] = round(50 + iog_factor * 100)
        stats['keyPasses'] = round(15 + iog_factor * 40)
    
    # Round all stats to integers
    return {k: max(0, int(round(v))) for k, v in stats.items()}

def update_players_file():
    """Update players.ts with generated stats."""
    players_file = Path("c:\\Users\\ahmed\\galactico11\\src\\data\\players.ts")
    
    # Read the file
    content = players_file.read_text(encoding='utf-8')
    
    # Extract players array
    match = re.search(r'export const players = \[(.*?)\];', content, re.DOTALL)
    if not match:
        print("ERROR: Could not find players array")
        return
    
    players_json = '[' + match.group(1) + ']'
    
    # Parse as JSON (with some replacements for JS syntax)
    players_json = re.sub(r'//.*$', '', players_json, flags=re.MULTILINE)  # Remove comments
    players_json = players_json.replace("'", '"')  # Single to double quotes
    
    try:
        players = json.loads(players_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse JSON: {e}")
        return
    
    # Generate stats for each player
    updated_count = 0
    for player in players:
        if 'stats' not in player or player['stats'] is None:
            positions = player.get('positions', [])
            iog = player.get('iog', 85)
            player['stats'] = generate_stats(player.get('name'), positions, iog)
            updated_count += 1
    
    print(f"Generated stats for {updated_count} players")
    
    # Rebuild the file content
    new_lines = ["export const players = ["]
    for i, player in enumerate(players):
        # Format player object
        line = "  { "
        line += f'id: {player["id"]}, '
        line += f'name: "{player["name"]}", '
        line += f'club: "{player["club"]}", '
        line += f'league: "{player["league"]}", '
        line += f'era: "{player["era"]}", '
        line += f'positions: {json.dumps(player["positions"])}, '
        line += f'iog: {player["iog"]}, '
        
        if 'image' in player and player['image']:
            line += f'image: "{player["image"]}", '
        
        # Add stats
        stats = player.get('stats', {})
        stats_str = "{ "
        stats_items = []
        for key in ['goals', 'assists', 'xG', 'xA', 'tackles', 'interceptions', 
                    'progressivePasses', 'progressiveCarries', 'keyPasses']:
            if key in stats:
                stats_items.append(f"{key}: {stats[key]}")
        stats_str += ", ".join(stats_items) + " }"
        line += f'stats: {stats_str}'
        
        line += " },"
        if i == len(players) - 1:
            line = line.rstrip(',')  # Remove trailing comma from last item
            line += " "
        new_lines.append(line)
    
    new_lines.append("];")
    
    new_content = "\n".join(new_lines)
    
    # Write back
    players_file.write_text(new_content, encoding='utf-8')
    print(f"Updated {players_file}")

if __name__ == '__main__':
    update_players_file()
