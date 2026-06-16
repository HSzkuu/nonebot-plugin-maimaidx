import json
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Union

import aiofiles
from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image, ImageDraw

from ..config import *
from .image import DrawText, image_to_base64, music_picture, tricolor_gradient
from .maimaidx_api_data import maiApi
from .maimaidx_error import *
from .maimaidx_model import PlayInfoDev
from .maimaidx_best_50 import coloumWidth, changeColumnWidth
from .maimaidx_music import mai


async def load_records() -> Dict:
    if not records_file.exists():
        return {}
    try:
        async with aiofiles.open(records_file, 'r', encoding='utf-8') as f:
            return json.loads(await f.read())
    except Exception:
        return {}


async def save_records(data: Dict) -> None:
    async with aiofiles.open(records_file, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=4))


async def save_user_records(qqid: int, records: List[PlayInfoDev], nickname: str = '') -> None:
    data = await load_records()
    data[str(qqid)] = {
        'nickname': nickname,
        'records': [r.model_dump() for r in records]
    }
    await save_records(data)


async def update_user_records(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str, int]:
    try:
        if username:
            qqid = None
        userinfo = await maiApi.query_user_get_dev(qqid=qqid, username=username)
        if not userinfo.records:
            return '该用户没有游玩记录'
        target_qqid = qqid or 0
        await save_user_records(target_qqid, userinfo.records, userinfo.nickname or '')
        return target_qqid
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        return str(e)
    except (TokenError, TokenDisableError, TokenNotFoundError) as e:
        return str(e)
    except Exception:
        log.error(traceback.format_exc())
        return f'未知错误：{type(e)}'


class DrawGroupRank:

    def __init__(self, title: str, entries: List[dict], total_dx: int = 1) -> None:
        self.title = title
        self.entries = entries
        self.total_dx = total_dx

    def draw(self) -> Image.Image:
        S = 2
        width = 1060 * S
        row_h = 75 * S
        header_h = 80 * S
        footer_h = 60 * S
        count = min(len(self.entries), 50)
        height = header_h + count * row_h + footer_h

        img = tricolor_gradient(width, height)
        dr = ImageDraw.Draw(img)
        sy = DrawText(dr, SIYUAN)
        tb = DrawText(dr, TBFONT)

        sy.draw(width // 2, 40 * S, 32 * S, self.title, (50, 50, 50, 255), 'mm')

        col_rank = 40 * S
        col_name = 110 * S
        col_achieve = 420 * S
        col_dx = 620 * S
        col_dxstar = 790 * S
        col_fc = 850 * S
        col_fs = 895 * S
        col_rate = 945 * S

        y = header_h
        for idx, entry in enumerate(self.entries[:50]):
            rank = idx + 1
            nickname = entry.get('nickname', str(entry.get('qqid', '???')))
            achieve = entry.get('achievements', 0)
            rate = entry.get('rate', '')
            fc = entry.get('fc', '')
            fs = entry.get('fs', '')
            dx_score = entry.get('dxScore', 0)
            dx_pct = dx_score / self.total_dx * 100 if self.total_dx else 0

            is_even = rank % 2 == 0
            row_color = (255, 255, 255, 255) if is_even else (50, 50, 50, 255)
            if is_even:
                overlay = Image.new('RGBA', (width - 20 * S, row_h - 2 * S), (0, 0, 0, 120))
                img.alpha_composite(overlay, (10 * S, y))

            rank_color = (200, 160, 0, 255) if rank <= 3 else ((255, 255, 255, 255) if is_even else (80, 80, 80, 255))
            tb.draw(col_rank, y + row_h // 2, 28 * S, f'#{rank}', rank_color, 'mm')

            name_display = nickname
            if coloumWidth(name_display) > 14:
                name_display = changeColumnWidth(name_display, 13) + '..'
            sy.draw(col_name, y + row_h // 2, 24 * S, name_display, row_color, 'lm')

            tb.draw(col_achieve, y + row_h // 2, 32 * S, f'{achieve:.4f}%', row_color, 'rm')

            tb.draw(col_dx, y + row_h // 2, 20 * S, f'{dx_score}/{self.total_dx} ({dx_pct:.1f}%)', row_color, 'mm')

            dx_num = 0
            if dx_pct > 97: dx_num = 5
            elif dx_pct > 95: dx_num = 4
            elif dx_pct > 93: dx_num = 3
            elif dx_pct > 90: dx_num = 2
            elif dx_pct > 85: dx_num = 1
            if dx_num:
                dx_icon = Image.open(maimaidir / f'UI_GAM_Gauge_DXScoreIcon_0{dx_num}.png').resize((57 * S, 32 * S))
                img.alpha_composite(dx_icon, (col_dxstar, y + row_h // 2 - 16 * S))

            if fc:
                fc_icon = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fcl.get(fc, fc)}.png').resize((38 * S, 38 * S))
                img.alpha_composite(fc_icon, (col_fc, y + row_h // 2 - 19 * S))

            if fs:
                fs_icon = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fsl.get(fs, fs)}.png').resize((38 * S, 38 * S))
                img.alpha_composite(fs_icon, (col_fs, y + row_h // 2 - 19 * S))

            if rate:
                rate_icon = Image.open(maimaidir / f'UI_TTR_Rank_{score_Rank_l.get(rate, rate)}.png').resize((75 * S, 33 * S))
                img.alpha_composite(rate_icon, (col_rate, y + row_h // 2 - 16 * S))

            y += row_h

        footer_y = header_h + count * row_h
        sy.draw(
            width // 2, footer_y + 30 * S, 16 * S,
            f'共计 {len(self.entries)} 人 · Designed by {maiconfig.botName} BOT',
            (120, 120, 120, 255), 'mm'
        )
        return img.resize((1060, height // S), Image.LANCZOS)


async def get_group_song_rank(
    bot,
    group_id: int,
    song_id: str,
    level_index: int = 3
) -> Union[MessageSegment, str]:
    music = mai.total_list.by_id(song_id)
    if music:
        song_id = music.id
    if not music:
        by_t = mai.total_list.by_title(song_id)
        if by_t:
            music = by_t
            song_id = music.id
    if not music:
        for m in mai.total_list:
            if song_id in m.title or m.title in song_id:
                music = m
                song_id = m.id
                break
    if not music:
        aliases = mai.total_alias_list.by_alias(song_id)
        if aliases:
            song_id = str(aliases[0].SongID)
            music = mai.total_list.by_id(song_id)
    if not music:
        return '未找到曲目'

    if level_index >= len(music.level):
        return f'该曲目没有这个等级'

    diff_names = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:MASTER']
    diff_name = diff_names[level_index]
    level_label = music.level[level_index]

    chart = music.charts[level_index]
    total_dx = sum(chart.notes) * 3

    try:
        members = await bot.get_group_member_list(group_id=group_id)
    except Exception:
        return '获取群成员列表失败'

    qqid_list = [str(m['user_id']) for m in members]
    all_records = await load_records()

    entries = []
    for qqid_str in qqid_list:
        user_data = all_records.get(qqid_str)
        if not user_data:
            continue
        nickname = user_data.get('nickname', qqid_str)
        for rec in user_data.get('records', []):
            if str(rec.get('song_id', '')) == str(song_id) and int(rec.get('level_index', -1)) == int(level_index):
                entries.append({
                    'qqid': qqid_str,
                    'nickname': nickname,
                    'achievements': rec.get('achievements', 0),
                    'rate': rec.get('rate', ''),
                    'fc': rec.get('fc', ''),
                    'fs': rec.get('fs', ''),
                    'dxScore': rec.get('dxScore', 0),
                })

    if not entries:
        return f'群内没有人记录过这首曲目 [{diff_name}]：{music.title}'

    entries.sort(key=lambda e: e['achievements'], reverse=True)

    drawer = DrawGroupRank(f'{music.title} [{diff_name}] · 群内排行榜', entries, total_dx)
    img = drawer.draw()
    return MessageSegment.image(image_to_base64(img))
