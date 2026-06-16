import math
import traceback
from io import BytesIO
from typing import Tuple, Union, overload

from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image, ImageDraw

from ..config import *
from .image import DrawText, image_to_base64, music_picture
from .maimaidx_api_data import maiApi
from .maimaidx_error import *
from .maimaidx_model import ChartInfo, Data, PlayInfoDefault, PlayInfoDev, UserInfo, UserInfoDev
from .maimaidx_music import mai


class ScoreBaseImage:
    
    text_color = (124, 129, 255, 255)
    t_color = [
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (138, 0, 226, 255)
    ]
    id_color = [
        (129, 217, 85, 255), 
        (245, 189, 21, 255),  
        (255, 129, 141, 255), 
        (159, 81, 220, 255),
        (138, 0, 226, 255)
    ]
    bg_color = [
        (111, 212, 61, 255), 
        (248, 183, 9, 255), 
        (255, 129, 141, 255), 
        (159, 81, 220, 255), 
        (219, 170, 255, 255)
    ]
    id_diff = [Image.new('RGBA', (55, 10), color) for color in bg_color]
    
    _diff = []
    _rise = []
    title_bg = None
    title_lengthen_bg = None
    design_bg = None
    aurora_bg = None
    shines_bg = None
    pattern_bg = None
    rainbow_bg = None
    rainbow_bottom_bg = None

    @classmethod
    def _load_image(cls):
        """将部分图片保存在内存"""
        cls._diff = [
            Image.open(maimaidir / 'b50_score_basic.png'), 
            Image.open(maimaidir / 'b50_score_advanced.png'), 
            Image.open(maimaidir / 'b50_score_expert.png'), 
            Image.open(maimaidir / 'b50_score_master.png'), 
            Image.open(maimaidir / 'b50_score_remaster.png')
        ]
        cls._rise = [
            Image.open(maimaidir / 'rise_score_basic.png'),
            Image.open(maimaidir / 'rise_score_advanced.png'),
            Image.open(maimaidir / 'rise_score_expert.png'),
            Image.open(maimaidir / 'rise_score_master.png'),
            Image.open(maimaidir / 'rise_score_remaster.png')
        ]
        cls.title_bg = Image.open(maimaidir / 'title.png')
        cls.title_lengthen_bg = Image.open(maimaidir / 'title-lengthen.png')
        cls.design_bg = Image.open(maimaidir / 'design.png')
        cls.aurora_bg = Image.open(maimaidir / 'aurora.png').convert('RGBA').resize((1400, 220))
        cls.shines_bg = Image.open(maimaidir / 'bg_shines.png').convert('RGBA')
        cls.pattern_bg = Image.open(maimaidir / 'pattern.png')
        cls.rainbow_bg = Image.open(maimaidir / 'rainbow.png').convert('RGBA')
        cls.rainbow_bottom_bg = Image.open(maimaidir / 'rainbow_bottom.png').convert('RGBA').resize((1200, 200))
    
    def __init__(self, image: Image.Image = None) -> None:
        if not maiconfig.saveinmem:
            self.load_image()
        
        if image is not None:
            self._im = image
            dr = ImageDraw.Draw(self._im)
            self._sy = DrawText(dr, SIYUAN)
            self._tb = DrawText(dr, TBFONT)
    
    def load_image(self):
        """在图片不保存在内存时使用"""
        self._diff = [
            Image.open(maimaidir / 'b50_score_basic.png'), 
            Image.open(maimaidir / 'b50_score_advanced.png'), 
            Image.open(maimaidir / 'b50_score_expert.png'), 
            Image.open(maimaidir / 'b50_score_master.png'), 
            Image.open(maimaidir / 'b50_score_remaster.png')
        ]
        self._rise = [
            Image.open(maimaidir / 'rise_score_basic.png'),
            Image.open(maimaidir / 'rise_score_advanced.png'),
            Image.open(maimaidir / 'rise_score_expert.png'),
            Image.open(maimaidir / 'rise_score_master.png'),
            Image.open(maimaidir / 'rise_score_remaster.png')
        ]
        self.title_bg = Image.open(maimaidir / 'title.png')
        self.title_lengthen_bg = Image.open(maimaidir / 'title-lengthen.png')
        self.design_bg = Image.open(maimaidir / 'design.png')
        self.aurora_bg = Image.open(maimaidir / 'aurora.png').convert('RGBA').resize((1400, 220))
        self.shines_bg = Image.open(maimaidir / 'bg_shines.png').convert('RGBA')
        self.pattern_bg = Image.open(maimaidir / 'pattern.png')
        self.rainbow_bg = Image.open(maimaidir / 'rainbow.png').convert('RGBA')
        self.rainbow_bottom_bg = Image.open(maimaidir / 'rainbow_bottom.png').convert('RGBA').resize((1200, 200))
    
    def whiledraw(
        self, 
        data: Union[List[ChartInfo], List[PlayInfoDefault], List[PlayInfoDev]], 
        dx: bool, 
        height: int = 0,
        start_y: Optional[int] = None
    ) -> None:
        """
        循环绘制成绩
        
        Params:
            `data`: 数据
            `dx`: 是否为新版本成绩
            `height`: 起始高度
            `start_y`: 自定义起始y坐标，优先于自动判断
        """
        # y为第一排纵向坐标，dy为各行间距
        dy = 114
        if start_y is not None:
            y = start_y
        elif data and type(data[0]) == ChartInfo:
            y = 1085 if dx else 235
        else:
            y = height
        for num, info in enumerate(data):
            if num % 5 == 0:
                x = 16
                y += dy if num != 0 else 0
            else:
                x += 276

            cover = Image.open(music_picture(info.song_id)).resize((75, 75))
            version = Image.open(maimaidir / f'{info.type.upper()}.png').resize((37, 14))
            if info.rate.islower():
                rate = Image.open(maimaidir / f'UI_TTR_Rank_{score_Rank_l[info.rate]}.png').resize((63, 28))
            else:
                rate = Image.open(maimaidir / f'UI_TTR_Rank_{info.rate}.png').resize((63, 28))

            self._im.alpha_composite(self._diff[info.level_index], (x, y))
            self._im.alpha_composite(cover, (x + 12, y + 12))
            self._im.alpha_composite(version, (x + 51, y + 91))
            self._im.alpha_composite(rate, (x + 92, y + 78))
            if info.fc:
                fc = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fcl[info.fc]}.png').resize((34, 34))
                self._im.alpha_composite(fc, (x + 154, y + 77))
            if info.fs:
                fs = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fsl[info.fs]}.png').resize((34, 34))
                self._im.alpha_composite(fs, (x + 185, y + 77))
            
            dxscore = sum(mai.total_list.by_id(str(info.song_id)).charts[info.level_index].notes) * 3
            dxnum = dxScore(info.dxScore / dxscore * 100)
            if dxnum:
                self._im.alpha_composite(
                    Image.open(maimaidir / f'UI_GAM_Gauge_DXScoreIcon_0{dxnum}.png').resize((47, 26)), (x + 217, y + 80)
                )

            self._tb.draw(x + 26, y + 98, 13, info.song_id, self.id_color[info.level_index], anchor='mm')
            title = info.title
            if coloumWidth(title) > 18:
                title = changeColumnWidth(title, 17) + '...'
            self._sy.draw(x + 93, y + 14, 14, title, self.t_color[info.level_index], anchor='lm')
            self._tb.draw(x + 93, y + 38, 30, f'{info.achievements:.4f}%', self.t_color[info.level_index], anchor='lm')
            self._tb.draw(x + 219, y + 65, 15, f'{info.dxScore}/{dxscore}', self.t_color[info.level_index], anchor='mm')
            self._tb.draw(x + 93, y + 65, 15, f'{info.ds} -> {info.ra}', self.t_color[info.level_index], anchor='lm')


class DrawBest(ScoreBaseImage):

    def __init__(self, UserInfo: UserInfo, qqid: Optional[Union[int, str]] = None, filter_name: Optional[str] = None, b40: bool = False) -> None:
        super().__init__(Image.open(maimaidir / 'b50_bg.png').convert('RGBA'))
        self.userName = UserInfo.nickname
        self.plate = UserInfo.plate
        self.addRating = UserInfo.additional_rating
        self.sdBest = UserInfo.charts.sd or []
        self.dxBest = UserInfo.charts.dx or []
        self.qqid = qqid
        self.filter_name = filter_name
        self.b40 = b40
        sdrating = sum([_.ra for _ in self.sdBest])
        dxrating = sum([_.ra for _ in self.dxBest])
        self.computedRa = sdrating + dxrating

    def _findRaPic(self) -> str:
        if self.b40:
            displayRa = self.computedRa + 2100
            if displayRa < 1000:
                num = '01'
            elif displayRa < 2000:
                num = '02'
            elif displayRa < 3000:
                num = '03'
            elif displayRa < 4000:
                num = '04'
            elif displayRa < 5000:
                num = '05'
            elif displayRa < 6000:
                num = '06'
            elif displayRa < 7000:
                num = '07'
            elif displayRa < 8000:
                num = '08'
            elif displayRa < 8500:
                num = '09'
            else:
                num = '11'
        else:
            if self.computedRa < 1000:
                num = '01'
            elif self.computedRa < 2000:
                num = '02'
            elif self.computedRa < 4000:
                num = '03'
            elif self.computedRa < 7000:
                num = '04'
            elif self.computedRa < 10000:
                num = '05'
            elif self.computedRa < 12000:
                num = '06'
            elif self.computedRa < 13000:
                num = '07'
            elif self.computedRa < 14000:
                num = '08'
            elif self.computedRa < 14500:
                num = '09'
            elif self.computedRa < 15000:
                num = '10'
            else:
                num = '11'
        return f'UI_CMN_DXRating_{num}.png'

    def _findMatchLevel(self) -> str:
        """
        寻找匹配等级图片
        
        Returns:
            `str` 返回图片名称
        """
        if self.addRating <= 10:
            num = f'{self.addRating:02d}'
        else:
            num = f'{self.addRating + 1:02d}'
        return f'UI_DNM_DaniPlate_{num}.png'

    async def draw(self) -> Image.Image:
        
        logo = Image.open(maimaidir / 'logo.png').resize((249, 120))
        dx_rating = Image.open(maimaidir / self._findRaPic()).resize((186, 35))
        Name = Image.open(maimaidir / 'Name.png')
        rating = Image.open(maimaidir / 'UI_CMN_Shougou_Rainbow.png').resize((270, 27))

        self._im.alpha_composite(logo, (14, 60))
        if self.plate:
            plate = Image.open(platedir / f'{self.plate}.png').resize((800, 130))
        else:
            plate = Image.open(maimaidir / 'UI_Plate_300501.png').resize((800, 130))
        self._im.alpha_composite(plate, (300, 60))
        icon = Image.open(maimaidir / 'UI_Icon_309503.png').resize((120, 120))
        self._im.alpha_composite(icon, (305, 65))
        if self.qqid:
            try:
                qqLogo = Image.open(BytesIO(await maiApi.qqlogo(qqid=self.qqid)))
                self._im.alpha_composite(qqLogo.convert('RGBA').resize((120, 120)), (305, 65))
            except Exception:
                pass
        self._im.alpha_composite(dx_rating, (435, 72))
        if self.b40:
            displayRa = self.computedRa + 2100
        else:
            displayRa = self.computedRa
        Rating = f'{displayRa:05d}'
        for n, i in enumerate(Rating):
            self._im.alpha_composite(
                Image.open(maimaidir / f'UI_NUM_Drating_{i}.png').resize((17, 20)), (520 + 15 * n, 80)
            )
        self._im.alpha_composite(Name, (435, 115))
        self._im.alpha_composite(rating, (435, 160))

        self._sy.draw(445, 135, 25, self.userName, (0, 0, 0, 255), 'lm')
        sdrating, dxrating = sum([_.ra for _ in self.sdBest]), sum([_.ra for _ in self.dxBest])
        
        if self.b40:
            self._tb.draw(
                570, 172, 17, 
                f'{sdrating} + {dxrating} + 2100 = {self.computedRa + 2100}', 
                (0, 0, 0, 255), 'mm', 3, (255, 255, 255, 255)
            )
        else:
            label = f'{self.filter_name} | ' if self.filter_name else ''
            self._tb.draw(
                570, 172, 17, 
                f'{label}B35: {sdrating} + B15: {dxrating} = {self.computedRa}', 
                (0, 0, 0, 255), 'mm', 3, (255, 255, 255, 255)
            )
        
        if self.filter_name:
            filter_text = self.filter_name
            if coloumWidth(filter_text) > 10:
                filter_text = changeColumnWidth(filter_text, 9) + '..'
            self._sy.draw(665, 89, 20, filter_text, (255, 255, 255, 255), 'mm', 2, (0, 0, 0, 255))
        
        self._sy.draw(
            700, 1570, 27, 
            f'Designed by Yuri-YuzuChaN & BlueDeer233. Generated by {maiconfig.botName} BOT', 
            self.text_color, 'mm', 5, (255, 255, 255, 255)
        )

        if self.b40:
            self.whiledraw(self.sdBest, False, start_y=235)
            dx_start = 235 + len(self.sdBest) // 5 * 114 + 40
            self.whiledraw(self.dxBest, True, start_y=dx_start)
        else:
            self.whiledraw(self.sdBest, False, start_y=235)
            self.whiledraw(self.dxBest, True, start_y=1085)

        return self._im


def dxScore(dx: int) -> int:
    """
    获取DX评分星星数量
    
    Params:
        `dx`: dx百分比
    Returns:
        `int` 返回星星数量
    """
    if dx <= 85:
        result = 0
    elif dx <= 90:
        result = 1
    elif dx <= 93:
        result = 2
    elif dx <= 95:
        result = 3
    elif dx <= 97:
        result = 4
    else:
        result = 5
    return result


def getCharWidth(o: int) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
        (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
        (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
        (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
        (120831, 1), (262141, 2), (1114109, 1),
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def coloumWidth(s: str) -> int:
    res = 0
    for ch in s:
        res += getCharWidth(ord(ch))
    return res


def changeColumnWidth(s: str, len: int) -> str:
    res = 0
    sList = []
    for ch in s:
        res += getCharWidth(ord(ch))
        if res <= len:
            sList.append(ch)
    return ''.join(sList)


@overload
def computeRa(ds: float, achievement: float) -> int:
    """
    计算底分
    
    Params:
        `ds`: 定数
        `achievement`: 成绩
    Returns:
        返回底分
    """
@overload
def computeRa(ds: float, achievement: float, *, onlyrate: bool = False) -> str:
    """
    计算评价
    
    Params:
        `ds`: 定数
        `achievement`: 成绩
        `onlyrate`: 是否只返回评价
    Returns:
        返回评价
    """
@overload
def computeRa(ds: float, achievement: float, *, israte: bool = False) -> Tuple[int, str]:
    """
    计算底分和评价
    
    Params:
        `ds`: 定数
        `achievement`: 成绩
        `israte`: 是否返回所有数据
    Returns:
        (底分, 评价)
    """
def computeRa(
    ds: float, 
    achievement: float, 
    *, 
    spp: bool = True,
    onlyrate: bool = False, 
    israte: bool = False
) -> Union[int, Tuple[int, str]]:
    if spp:
        if achievement < 50:
            baseRa = 7.0
        elif achievement < 60:
            baseRa = 8.0
        elif achievement < 70:
            baseRa = 9.6
        elif achievement < 75:
            baseRa = 11.2
        elif achievement < 80:
            baseRa = 12.0
        elif achievement < 90:
            baseRa = 13.6
        elif achievement < 94:
            baseRa = 15.2
        elif achievement < 97:
            baseRa = 16.8
        elif achievement < 98:
            baseRa = 20.0
        elif achievement < 99:
            baseRa = 20.3
        elif achievement < 99.5:
            baseRa = 20.8
        elif achievement < 100:
            baseRa = 21.1
        elif achievement < 100.5:
            baseRa = 21.6
        else:
            baseRa = 22.4
    else:
        if achievement < 50:
            baseRa = 0.0
        elif achievement < 60:
            baseRa = 5.0
        elif achievement < 70:
            baseRa = 6.0
        elif achievement < 75:
            baseRa = 7.0
        elif achievement < 80:
            baseRa = 7.5
        elif achievement < 90:
            baseRa = 8.5
        elif achievement < 94:
            baseRa = 9.5
        elif achievement < 97:
            baseRa = 10.5
        elif achievement < 98:
            baseRa = 12.5
        elif achievement < 99:
            baseRa = 12.7
        elif achievement < 99.5:
            baseRa = 13.0
        elif achievement < 100:
            baseRa = 13.2
        elif achievement < 100.5:
            baseRa = 13.5
        else:
            baseRa = 14.0

    if achievement < 50:
        rate = 'D'
    elif achievement < 60:
        rate = 'C'
    elif achievement < 70:
        rate = 'B'
    elif achievement < 75:
        rate = 'BB'
    elif achievement < 80:
        rate = 'BBB'
    elif achievement < 90:
        rate = 'A'
    elif achievement < 94:
        rate = 'AA'
    elif achievement < 97:
        rate = 'AAA'
    elif achievement < 98:
        rate = 'S'
    elif achievement < 99:
        rate = 'Sp'
    elif achievement < 99.5:
        rate = 'SS'
    elif achievement < 100:
        rate = 'SSp'
    elif achievement < 100.5:
        rate = 'SSS'
    else:
        rate = 'SSSp'

    if israte:
        data = (math.floor(ds * (min(100.5, achievement) / 100) * baseRa), rate)
    elif onlyrate:
        data = rate
    else:
        data = math.floor(ds * (min(100.5, achievement) / 100) * baseRa)

    return data


async def generate(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[MessageSegment, str]:
    """
    生成b50
    
    Params:
        `qqid`: QQ号
        `username`: 用户名
    Returns:
        `Union[MessageSegment, str]`
    """
    try:
        if username:
            qqid = None
        userinfo = await maiApi.query_user_get_dev(qqid=qqid, username=username)
        
        if not userinfo.records:
            return '该用户没有游玩记录'
        
        if qqid:
            from .maimaidx_records import save_user_records
            await save_user_records(qqid, userinfo.records, userinfo.nickname or '')
        
        def _sort_key(r):
            chart = mai.total_list.by_id(str(r.song_id))
            dxscore = sum(chart.charts[r.level_index].notes) * 3 if chart else 1
            dx_pct = r.dxScore / dxscore * 100
            return (r.ra, r.achievements, dx_pct)
        
        def _is_dx(r):
            music = mai.total_list.by_id(str(r.song_id))
            return music.basic_info.is_new if music else False
        
        sd_records = sorted([r for r in userinfo.records if not _is_dx(r)], key=_sort_key, reverse=True)[:35]
        dx_records = sorted([r for r in userinfo.records if _is_dx(r)], key=_sort_key, reverse=True)[:15]
        
        user_info = UserInfo(
            additional_rating=userinfo.additional_rating,
            nickname=userinfo.nickname,
            plate=userinfo.plate,
            rating=userinfo.rating,
            username=userinfo.username,
            charts=Data(sd=sd_records, dx=dx_records)
        )
        
        draw_best = DrawBest(user_info, qqid)
        
        msg = MessageSegment.image(image_to_base64(await draw_best.draw()))
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        msg = str(e)
    except (TokenError, TokenDisableError, TokenNotFoundError) as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg


async def generate_b40(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[MessageSegment, str]:
    """
    生成b40 (25 SD + 15 DX, 旧版RA算法)
    """
    try:
        if username:
            qqid = None
        userinfo = await maiApi.query_user_get_dev(qqid=qqid, username=username)
        
        if not userinfo.records:
            return '该用户没有游玩记录'
        
        if qqid:
            from .maimaidx_records import save_user_records
            await save_user_records(qqid, userinfo.records, userinfo.nickname or '')
        
        def _calc_ra(r):
            chart = mai.total_list.by_id(str(r.song_id))
            ds = chart.ds[r.level_index] if chart else r.ds
            return computeRa(ds, r.achievements, spp=False)
        
        def _sort_key(r):
            return (_calc_ra(r), r.achievements)
        
        def _is_dx(r):
            music = mai.total_list.by_id(str(r.song_id))
            return music.basic_info.is_new if music else False
        
        for r in userinfo.records:
            r.ra = _calc_ra(r)
        
        sd_records = sorted([r for r in userinfo.records if not _is_dx(r)], key=_sort_key, reverse=True)[:25]
        dx_records = sorted([r for r in userinfo.records if _is_dx(r)], key=_sort_key, reverse=True)[:15]
        
        user_info = UserInfo(
            additional_rating=userinfo.additional_rating,
            nickname=userinfo.nickname,
            plate=userinfo.plate,
            rating=userinfo.rating,
            username=userinfo.username,
            charts=Data(sd=sd_records, dx=dx_records)
        )
        
        draw_best = DrawBest(user_info, qqid, b40=True)
        
        msg = MessageSegment.image(image_to_base64(await draw_best.draw()))
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        msg = str(e)
    except (TokenError, TokenDisableError, TokenNotFoundError) as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg


def parse_filter(filter_type: str):
    """
    解析过滤器类型，返回 (过滤函数, 显示名称)
    
    支持的过滤器:
        空: 不过滤(用于allb50)
        fc类: ap(ap+app), ap+(app), fc(fc+fcp+ap+app), fc+(fcp+ap+app)
        难度类: {level}l, {level}+l (level为1-15)
        评级类: a, aa, aaa, s, s+, ss, ss+, sss, sss+
    
    Returns:
        `Tuple[Callable, str]` (过滤函数, 显示名称)
    """
    ft = filter_type.lower()
    
    if not ft:
        return (lambda r: True, 'B50')
    elif ft == 'ap':
        return (lambda r: r.fc in ('ap', 'app'), 'AP 50')
    elif ft == 'ap+':
        return (lambda r: r.fc == 'app', 'AP+ 50')
    elif ft == 'fc':
        return (lambda r: r.fc in ('fc', 'fcp', 'ap', 'app'), 'FC 50')
    elif ft == 'fc+':
        return (lambda r: r.fc in ('fcp', 'ap', 'app'), 'FC+ 50')
    elif ft.endswith('l'):
        level = ft[:-1]
        if not level:
            raise ValueError('Invalid filter type')
        return (lambda r: r.level == level, f'{level}L 50')
    else:
        rate_val = ft.replace('+', 'p')
        display = ft.upper()
        rate_order = ['a', 'aa', 'aaa', 's', 'sp', 'ss', 'ssp', 'sss', 'sssp']
        if rate_val in rate_order:
            min_idx = rate_order.index(rate_val)
            valid_rates = set(rate_order[min_idx:])
            return (lambda r: r.rate in valid_rates, f'{display} 50')
        return (lambda r: r.rate == rate_val, f'{display} 50')


class DrawFilterBest(ScoreBaseImage):

    def __init__(
        self, 
        userinfo: UserInfoDev, 
        records: List[PlayInfoDev], 
        filter_name: str,
        qqid: Optional[Union[int, str]] = None
    ) -> None:
        super().__init__(Image.open(maimaidir / 'b50_bg.png').convert('RGBA'))
        self.userName = userinfo.nickname
        self.plate = userinfo.plate
        self.addRating = userinfo.additional_rating
        self.records = records
        self.filter_name = filter_name
        self.qqid = qqid
        self.computedRa = sum([_.ra for _ in self.records])

    def _findRaPic(self) -> str:
        if self.computedRa < 1000:
            num = '01'
        elif self.computedRa < 2000:
            num = '02'
        elif self.computedRa < 4000:
            num = '03'
        elif self.computedRa < 7000:
            num = '04'
        elif self.computedRa < 10000:
            num = '05'
        elif self.computedRa < 12000:
            num = '06'
        elif self.computedRa < 13000:
            num = '07'
        elif self.computedRa < 14000:
            num = '08'
        elif self.computedRa < 14500:
            num = '09'
        elif self.computedRa < 15000:
            num = '10'
        else:
            num = '11'
        return f'UI_CMN_DXRating_{num}.png'

    def _findMatchLevel(self) -> str:
        if self.addRating <= 10:
            num = f'{self.addRating:02d}'
        else:
            num = f'{self.addRating + 1:02d}'
        return f'UI_DNM_DaniPlate_{num}.png'

    async def draw(self) -> Image.Image:
        
        logo = Image.open(maimaidir / 'logo.png').resize((249, 120))
        dx_rating = Image.open(maimaidir / self._findRaPic()).resize((186, 35))
        Name = Image.open(maimaidir / 'Name.png')
        rating = Image.open(maimaidir / 'UI_CMN_Shougou_Rainbow.png').resize((270, 27))

        self._im.alpha_composite(logo, (14, 60))
        if self.plate:
            plate = Image.open(platedir / f'{self.plate}.png').resize((800, 130))
        else:
            plate = Image.open(maimaidir / 'UI_Plate_300501.png').resize((800, 130))
        self._im.alpha_composite(plate, (300, 60))
        icon = Image.open(maimaidir / 'UI_Icon_309503.png').resize((120, 120))
        self._im.alpha_composite(icon, (305, 65))
        if self.qqid:
            try:
                qqLogo = Image.open(BytesIO(await maiApi.qqlogo(qqid=self.qqid)))
                self._im.alpha_composite(qqLogo.convert('RGBA').resize((120, 120)), (305, 65))
            except Exception:
                pass
        self._im.alpha_composite(dx_rating, (435, 72))
        Rating = f'{self.computedRa:05d}'
        for n, i in enumerate(Rating):
            self._im.alpha_composite(
                Image.open(maimaidir / f'UI_NUM_Drating_{i}.png').resize((17, 20)), (520 + 15 * n, 80)
            )
        self._im.alpha_composite(Name, (435, 115))
        self._im.alpha_composite(rating, (435, 160))

        self._sy.draw(445, 135, 25, self.userName, (0, 0, 0, 255), 'lm')
        self._tb.draw(
            570, 172, 17, 
            f'RA: {self.computedRa}', 
            (0, 0, 0, 255), 'mm', 3, (255, 255, 255, 255)
        )
        filter_text = self.filter_name
        if coloumWidth(filter_text) > 10:
            filter_text = changeColumnWidth(filter_text, 9) + '..'
        self._sy.draw(665, 89, 20, filter_text, (255, 255, 255, 255), 'mm', 2, (0, 0, 0, 255))
        self._sy.draw(
            700, 1570, 27, 
            f'Designed by Yuri-YuzuChaN & BlueDeer233. Generated by {maiconfig.botName} BOT', 
            self.text_color, 'mm', 5, (255, 255, 255, 255)
        )

        self.whiledraw(self.records, False, start_y=235)

        return self._im


async def generate_filtered(
    qqid: Optional[int] = None, 
    username: Optional[str] = None, 
    filter_type: str = '',
    all_mode: bool = False
) -> Union[MessageSegment, str]:
    """
    生成过滤后的best50
    
    Params:
        `qqid`: QQ号
        `username`: 用户名
        `filter_type`: 过滤器类型 (空/ap/ap+/fc/fc+/{level}l/{level}+l/a/aa/aaa/s/s+/ss/ss+/sss/sss+)
        `all_mode`: True时不区分SD/DX全部显示在一个区域，False时按B50布局(B35+B15)
    Returns:
        `Union[MessageSegment, str]`
    """
    try:
        if username:
            qqid = None
        userinfo = await maiApi.query_user_get_dev(qqid=qqid, username=username)
        
        if not userinfo.records:
            return '该用户没有游玩记录'
        
        if qqid:
            from .maimaidx_records import save_user_records
            await save_user_records(qqid, userinfo.records, userinfo.nickname or '')
        
        filter_func, filter_name = parse_filter(filter_type)
        
        filtered = [r for r in userinfo.records if filter_func(r)]
        
        if not filtered:
            return f'没有找到满足条件 [{filter_name}] 的记录'
        
        def _sort_key(r):
            chart = mai.total_list.by_id(str(r.song_id))
            dxscore = sum(chart.charts[r.level_index].notes) * 3 if chart else 1
            dx_pct = r.dxScore / dxscore * 100
            return (r.ra, r.achievements, dx_pct)
        
        filtered.sort(key=_sort_key, reverse=True)
        
        if all_mode:
            top50 = filtered[:50]
            draw = DrawFilterBest(userinfo, top50, filter_name, qqid)
            msg = MessageSegment.image(image_to_base64(await draw.draw()))
        else:
            def _is_dx(r):
                music = mai.total_list.by_id(str(r.song_id))
                return music.basic_info.is_new if music else False
            
            sd_records = [r for r in filtered if not _is_dx(r)][:35]
            dx_records = [r for r in filtered if _is_dx(r)][:15]
            
            user_info = UserInfo(
                additional_rating=userinfo.additional_rating,
                nickname=userinfo.nickname,
                plate=userinfo.plate,
                rating=userinfo.rating,
                username=userinfo.username,
                charts=Data(sd=sd_records, dx=dx_records)
            )
            
            draw_best = DrawBest(user_info, qqid, filter_name=filter_name)
            msg = MessageSegment.image(image_to_base64(await draw_best.draw()))
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        msg = str(e)
    except (TokenError, TokenDisableError, TokenNotFoundError) as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg