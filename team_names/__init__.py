from pyplanet.apps.config import AppConfig
from pyplanet.contrib.command import Command

class TeamNamesManager(AppConfig):
    name = 'team_names'
    app_dependencies = ['core.maniaplanet']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_start(self):
        await self.instance.permission_manager.register('admin', 'Set team names', app=self, min_level=2)
        await self.instance.command_manager.register(
            Command(command='teamname', target=self.set_team_name_attempt, perms='team_names:admin', admin=True, description="Set the name of a team.($i//teamname 'team' 'name'. $z$s team => 0 or 1, name => e.g. $$f0fTEAM1).")
            .add_param(name='team', required=True).add_param(name='name', required=True),
        )

    async def set_team_name_attempt(self, player, data = None, **kwargs):
        current_script = await self.instance.mode_manager.get_current_script()
        if not self.is_team_mode(current_script):
            await self.instance.chat(f'$f00Command available only for team mode !', player.login)
        else:
            if data.team == '0' or data.team == '1':
                await self.set_team_name(player, data)
            else:
                await self.instance.chat(f'$f00Team {data.team} unknown. Please use $i0 $z$s$F00 or $i1 $z$s$f00!', player.login)
    
    async def set_team_name(self, player, data):
        prev_team_info = await self.instance.gbx('GetTeamInfo', int(data.team) + 1)

        if data.name.startswith('$'):
            # Extract name
            team_name = data.name[4:]    
            # Extract color code
            tm_hex = data.name[0:4]
            # Get hue value from tm hex color
            team_color = self.tmhex_to_tmhue(tm_hex)
        else:
            team_name = data.name
            team_color = prev_team_info["HuePrimary"]
            tm_hex = '$' + prev_team_info["RGB"]

        # Get the opponent team info
        oppo_team_info = await self.instance.gbx('GetTeamInfo', 2 if data.team == '0' else 1)
        oppo_team_name = oppo_team_info["Name"]
        oppo_team_color = oppo_team_info["HuePrimary"]

        # Set teams name and color
        if data.team == '0':
            await self.instance.gbx('SetTeamInfo', 'unused', 0.1, 'World', team_name, team_color, '', oppo_team_name, oppo_team_color, '')
        elif data.team == '1':
            await self.instance.gbx('SetTeamInfo', 'unused', 0.1, 'World', oppo_team_name, oppo_team_color, '', team_name, team_color, '')

        # Notify everybody the change in the chat
        await self.instance.chat(f'{player.nickname} $z$s$FF0replaced team name ${prev_team_info["RGB"] + prev_team_info["Name"]}$z$s$FF0 by {tm_hex + team_name}$z$s$FF0!')

    def is_team_mode(self, mode):
        mode = mode.lower()
        return mode.startswith('team') or mode.startswith('trackmania/tm_teams_online')

    def tmhex_to_tmhue(self, tmhex):
        six_hex = self.three_hex_to_six_hex(tmhex)
        rgb = self.hex_to_rgb(six_hex.lstrip('#'))
        hsl = self.rgb_to_hsv(rgb[0], rgb[1], rgb[2])
        tmhue = self.hsv_to_tmhue(hsl[0])
        return tmhue

    def three_hex_to_six_hex(self, hex):
        return '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3]
    
    def hex_to_rgb(self, hex):
        return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hsv(self, r, g, b):
        r, g, b = r/255.0, g/255.0, b/255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx-mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g-b)/df) + 360) % 360
        elif mx == g:
            h = (60 * ((b-r)/df) + 120) % 360
        elif mx == b:
            h = (60 * ((r-g)/df) + 240) % 360
        if mx == 0:
            s = 0
        else:
            s = (df/mx)*100
        v = mx*100

        return h, s, v

    def hsv_to_tmhue(self, h):
        return h/360

    