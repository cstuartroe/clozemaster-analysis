import argparse
import json
import re
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
import os
from tqdm import tqdm
from typing import Callable, Iterable, Optional, Union

from bs4 import BeautifulSoup as bs
import requests

from shared import Exercise, all_exercises, TokenManager, get_wiktionary_section


def load_secondary_joyo():
    res = requests.get("https://en.wikipedia.org/wiki/List_of_j%C5%8Dy%C5%8D_kanji")
    soup = bs(res.text, features="html.parser")
    table = soup.find("table", {"class": "sortable wikitable"})
    rows = table.tbody.find_all("tr")[1:]

    for row in rows:
        _, new, _, _, _, grade, _, _, _ = row.find_all("td")
        if grade.text == "S":
            print(new.text[0], end='')

    print()


JOYO = {
    1: (
        "一九七二人入八力十下三千上口土夕大女子小山川五天中六円手文日月木水火犬王正出本右"
        "四左玉生田白目石立百年休先名字早気竹糸耳虫村男町花見貝赤足車学林空金雨青草音校森"
    ),
    2: (
        "刀万丸才工弓内午少元今公分切友太引心戸方止毛父牛半市北古台兄冬外広母用矢交会合同"
        "回寺地多光当毎池米羽考肉自色行西来何作体弟図声売形汽社角言谷走近里麦画東京夜直国"
        "姉妹岩店明歩知長門昼前南点室後春星海活思科秋茶計風食首夏弱原家帰時紙書記通馬高強"
        "教理細組船週野雪魚鳥黄黒場晴答絵買朝道番間雲園数新楽話遠電鳴歌算語読聞線親頭曜顔"
    ),
    3: (
        "丁予化区反央平申世由氷主仕他代写号去打皮皿礼両曲向州全次安守式死列羊有血住助医君"
        "坂局役投対決究豆身返表事育使命味幸始実定岸所放昔板泳注波油受物具委和者取服苦重乗"
        "係品客県屋炭度待急指持拾昭相柱洋畑界発研神秒級美負送追面島勉倍真員宮庫庭旅根酒消"
        "流病息荷起速配院悪商動宿帳族深球祭第笛終習転進都部問章寒暑植温湖港湯登短童等筆着"
        "期勝葉落軽運遊開階陽集悲飲歯業感想暗漢福詩路農鉄意様緑練銀駅鼻横箱談調橋整薬館題"
    ),
    4: (
        "士不夫欠氏民史必失包末未以付令加司功札辺印争仲伝共兆各好成灯老衣求束兵位低児冷別"
        "努労告囲完改希折材利臣良芸初果刷卒念例典周協参固官底府径松毒泣治法牧的季英芽単省"
        "変信便軍勇型建昨栄浅胃祝紀約要飛候借倉孫案害帯席徒挙梅残殺浴特笑粉料差脈航訓連郡"
        "巣健側停副唱堂康得救械清望産菜票貨敗陸博喜順街散景最量満焼然無給結覚象貯費達隊飯"
        "働塩戦極照愛節続置腸辞試歴察旗漁種管説関静億器賞標熱養課輪選機積録観類験願鏡競議"
    ),
    5: (
        "久仏支比可旧永句圧弁布刊犯示再仮件任因団在舌似余判均志条災応序快技状防武承価舎券"
        "制効妻居往性招易枝河版肥述非保厚故政査独祖則逆退迷限師個修俵益能容恩格桜留破素耕"
        "財造率貧基婦寄常張術情採授接断液混現略眼務移経規許設責険備営報富属復提検減測税程"
        "絶統証評賀貸貿過勢幹準損禁罪義群墓夢解豊資鉱預飼像境増徳慣態構演精総綿製複適酸銭"
        "銅際雑領導敵暴潔確編賛質興衛燃築輸績講謝織職額識護"
    ),
    6: (
        "亡寸己干仁尺片冊収処幼庁穴危后灰吸存宇宅机至否我系卵忘孝困批私乱垂乳供並刻呼宗宙"
        "宝届延忠拡担拝枚沿若看城奏姿宣専巻律映染段洗派皇泉砂紅背肺革蚕値俳党展座従株将班"
        "秘純納胸朗討射針降除陛骨域密捨推探済異盛視窓翌脳著訪訳欲郷郵閉頂就善尊割創勤裁揮"
        "敬晩棒痛筋策衆装補詞貴裏傷暖源聖盟絹署腹蒸幕誠賃疑層模穀磁暮誤誌認閣障劇権潮熟蔵"
        "諸誕論遺奮憲操樹激糖縦鋼厳優縮覧簡臨難臓警"
    ),
    "primary places": (
        "茨媛岡潟岐熊香佐埼崎滋鹿縄井沖栃奈梨阪阜"
    ),
    7: (
        "亜哀挨曖握扱宛嵐依威為畏尉萎偉椅彙違維慰緯壱逸芋咽姻淫陰隠韻唄鬱畝浦詠影鋭疫悦越"
        "謁閲炎怨宴援煙猿鉛縁艶汚凹押旺欧殴翁奥憶臆虞乙俺卸穏佳苛架華菓渦嫁暇禍靴寡箇稼蚊"
        "牙瓦雅餓介戒怪拐悔皆塊楷潰壊懐諧劾崖涯慨蓋該概骸垣柿核殻郭較隔獲嚇穫岳顎掛括喝渇"
        "葛滑褐轄且釜鎌刈甘汗缶肝冠陥乾勘患貫喚堪換敢棺款閑勧寛歓監緩憾還環韓艦鑑含玩頑企"
        "伎忌奇祈軌既飢鬼亀幾棋棄毀畿輝騎宜偽欺儀戯擬犠菊吉喫詰却脚虐及丘朽臼糾嗅窮巨拒拠"

        "虚距御凶叫狂享況峡挟狭恐恭脅矯響驚仰暁凝巾斤菌琴僅緊錦謹襟吟駆惧愚偶遇隅串屈掘窟"
        "繰勲薫刑茎契恵啓掲渓蛍傾携継詣慶憬稽憩鶏迎鯨隙撃桁傑肩倹兼剣拳軒圏堅嫌献遣賢謙鍵"
        "繭顕懸幻玄弦舷股虎孤弧枯雇誇鼓錮顧互呉娯悟碁勾孔巧甲江坑抗攻更拘肯侯恒洪荒郊貢控"
        "梗喉慌硬絞項溝綱酵稿衡購乞拷剛傲豪克酷獄駒込頃昆恨婚痕紺魂墾懇沙唆詐鎖挫采砕宰栽"
        "彩斎債催塞歳載剤削柵索酢搾錯咲刹拶撮擦桟惨傘斬暫旨伺刺祉肢施恣脂紫嗣雌摯賜諮侍慈"

        "餌璽軸𠮟疾執湿嫉漆芝赦斜煮遮邪蛇酌釈爵寂朱狩殊珠腫趣寿呪需儒囚舟秀臭袖羞愁酬醜蹴"
        "襲汁充柔渋銃獣叔淑粛塾俊瞬旬巡盾准殉循潤遵庶緒如叙徐升召匠床抄肖尚昇沼宵症祥称渉"
        "紹訟掌晶焦硝粧詔奨詳彰憧衝償礁鐘丈冗浄剰畳壌嬢錠譲醸拭殖飾触嘱辱尻伸芯辛侵津唇娠"
        "振浸紳診寝慎審震薪刃尽迅甚陣尋腎須吹炊帥粋衰酔遂睡穂随髄枢崇据杉裾瀬是姓征斉牲凄"
        "逝婿誓請醒斥析脊隻惜戚跡籍拙窃摂仙占扇栓旋煎羨腺詮践箋潜遷薦繊鮮禅漸膳繕狙阻租措"

        "粗疎訴塑遡礎双壮荘捜挿桑掃曹曽爽喪痩葬僧遭槽踪燥霜騒藻憎贈即促捉俗賊遜汰妥唾堕惰"
        "駄耐怠胎泰堆袋逮替滞戴滝択沢卓拓託濯諾濁但脱奪棚誰丹旦胆淡嘆端綻鍛弾壇恥致遅痴稚"
        "緻畜逐蓄秩窒嫡抽衷酎鋳駐弔挑彫眺釣貼超跳徴嘲澄聴懲勅捗沈珍朕陳鎮椎墜塚漬坪爪鶴呈"
        "廷抵邸亭貞帝訂逓偵堤艇締諦泥摘滴溺迭哲徹撤添塡殿斗吐妬途渡塗賭奴怒到逃倒凍唐桃透"
        "悼盗陶塔搭棟痘筒稲踏謄藤闘騰洞胴瞳峠匿督篤凸突屯豚頓貪鈍曇丼那謎鍋軟尼弐匂虹尿妊"

        "忍寧捻粘悩濃把覇婆罵杯排廃輩培陪媒賠伯拍泊迫剝舶薄漠縛爆箸肌鉢髪伐抜罰閥氾帆汎伴"
        "畔般販斑搬煩頒範繁藩蛮盤妃彼披卑疲被扉碑罷避尾眉微膝肘匹泌姫漂苗描猫浜賓頻敏瓶扶"
        "怖附訃赴浮符普腐敷膚賦譜侮舞封伏幅覆払沸紛雰噴墳憤丙併柄塀幣弊蔽餅壁璧癖蔑偏遍哺"
        "捕舗募慕簿芳邦奉抱泡胞俸倣峰砲崩蜂飽褒縫乏忙坊妨房肪某冒剖紡傍帽貌膨謀頰朴睦僕墨"
        "撲没勃堀奔翻凡盆麻摩磨魔昧埋膜枕又抹慢漫魅岬蜜妙眠矛霧娘冥銘滅免麺茂妄盲耗猛網黙"

        "紋冶弥厄躍闇喩愉諭癒唯幽悠湧猶裕雄誘憂融与誉妖庸揚揺溶腰瘍踊窯擁謡抑沃翼拉裸羅雷"
        "頼絡酪辣濫藍欄吏痢履璃離慄柳竜粒隆硫侶虜慮了涼猟陵僚寮療瞭糧厘倫隣瑠涙累塁励戻鈴"
        "零霊隷齢麗暦劣烈裂恋廉錬呂炉賂露弄郎浪廊楼漏籠麓賄脇惑枠湾腕"
    )
}


HIRAGANA_TABLE = {
    '': 'あいうえお',
    'k': 'かきくけこ',
    's': 'さしすせそ',
    't': 'たちつてと',
    'n': 'なにぬねの',
    'h': 'はひふへほ',
    'm': 'まみむめも',
    'y': 'や ゆ よ',
    'r': 'らりるれろ',
    'w': 'わゐ ゑを',
    'g': 'がぎぐげご',
    'z': 'ざじずぜぞ',
    'd': 'だぢづでど',
    'b': 'ばびぶべぼ',
    'p': 'ぱぴぷぺぽ',
    '-': 'ぁ  ぇ ',
    '-y': 'ゃ ゅ ょ',
}

KATAKANA_TABLE = {
    '': 'アイウエオ',
    'k': 'カキクケコ',
    's': 'サシスセソ',
    't': 'タチツテト',
    'n': 'ナニヌネノ',
    'h': 'ハヒフヘホ',
    'm': 'マミムメモ',
    'y': 'ヤ ユ ヨ',
    'r': 'ラリルレロ',
    'w': 'ワヰ ヱヲ',
    'g': 'ガギグゲゴ',
    'z': 'ザジズゼゾ',
    'd': 'ダヂヅデド',
    'b': 'バビブベボ',
    'p': 'パピプペポ',
    '-': 'ァィゥェォ',
    '-y': 'ャ ュ ョ',
    'v': '  ヴ  '
}

VOWELS = 'aiueo'


TRANSCRIPTION_REPLACEMENTS = {
    'hu': 'fu',
    'tu': 'tsu',
    'du': 'zu',
    'si': 'shi',
    'ti': 'chi',
    'di': 'ji',
    'zi': 'ji',
}


def phonemic_kana_table(table) -> dict[str, str]:
    return {
        kana: c + VOWELS[i]
        for c, kanas in table.items()
        for i, kana in enumerate(kanas)
        if kana != ' '
    }


def transcription(s: str) -> str:
    return TRANSCRIPTION_REPLACEMENTS.get(s, s)


def replace_table(table) -> dict[str, str]:
    return {
        k: transcription(v)
        for k, v in table.items()
    }


PHONEMIC_HIRAGANA_TRANSCRIPTIONS: dict[str, str] = {
    **phonemic_kana_table(HIRAGANA_TABLE),
    'ん': 'N',
    'っ': 'Q',
}


HIRAGANA_TRANSCRIPTIONS: dict[str, str] = replace_table(PHONEMIC_HIRAGANA_TRANSCRIPTIONS)


KATAKANA_TRANSCRIPTIONS: dict[str, str] = replace_table({
    **phonemic_kana_table(KATAKANA_TABLE),
    'ン': 'N',
    'ッ': 'Q',
    'ー': 'chōonpu',
})


def phonemic_transcribe_hiragana(s: str) -> str:
    out = ''
    for c in s:
        t = PHONEMIC_HIRAGANA_TRANSCRIPTIONS[c]
        prev = out[-1] if out else None
        if t[0] == '-':
            if t[1] == 'y':
                assert prev == 'i'
                out = out[:-1] + t[1:]
            else:
                raise ValueError(f"Unknown continuation character: {s}")
        else:
            if t[0] in 'aiueo' and prev == 'N':
                out += '\''
            elif out and prev == 'Q':
                assert t[0] in 'ksctp'
                out = out[:-1] + t[0]

            out += t

    return out


def parse_onset(transription: str) -> tuple[str, str]:
    onset = re.match('[kgsztdcjnhfpbmyrw]*', transription).group()
    return onset, transription[len(onset):]


class CharacterType(Enum):
    ASCII = "ASCII"
    JPUNCT = "CJK punctuation"
    HIRAGANA = "hiragana"
    KATAKANA = "katakana"
    KANJI = "kanji"
    FULLWIDTH = "fullwidth ASCII"
    SPECIAL = "special"
    OTHER = "other"


def ctype(c: str) -> CharacterType:
    o = ord(c)

    if c in "々ヶヵ・":
        return CharacterType.SPECIAL

    if 0x3000 <= o <= 0x303F:
        return CharacterType.JPUNCT

    if 0x3040 <= o <= 0x309F:
        return CharacterType.HIRAGANA

    if 0x30A0 <= o <= 0x30FF:
        return CharacterType.KATAKANA

    if 0x4E00 <= o <= 0x9FFF:
        return CharacterType.KANJI

    if 0xFF00 <= o <= 0xFF5F:
        return CharacterType.FULLWIDTH

    if o <= 0x007F:
        return CharacterType.ASCII

    return CharacterType.OTHER


TRANSCRIPTIONS: dict[CharacterType, dict[str, str]] = {
    CharacterType.HIRAGANA: HIRAGANA_TRANSCRIPTIONS,
    CharacterType.KATAKANA: KATAKANA_TRANSCRIPTIONS,
}


WELL_TESTING_THRESHOLD = 3


def load_joyo(max_level=6) -> set[str]:
    out = set()

    for level in JOYO.keys():
        overlap = set(JOYO[level]) & out
        if len(overlap) > 0:
            raise ValueError(f"Overlapping sets for level {level}: {', '.join(overlap)}")

        out.update(JOYO[level])

        if level == max_level:
            return out


@dataclass
class Reading:
    kanji: str
    kana: Optional[str]

    def __post_init__(self):
        assert all((ctype(c) is CharacterType.KANJI or c == '々') for c in self.kanji)
        if self.kana:
            assert all((ctype(c) is CharacterType.HIRAGANA or c == 'ー') for c in self.kana)

    def __str__(self):
        return f"{self.kanji}【{self.kana}】"

    def __hash__(self):
        return str(self).__hash__()


class ReadingsParser:
    def __init__(self, e: Exercise):
        self.pronunciation = e.pronunciation
        self.i = None

    def next(self):
        if self.i < len(self.pronunciation):
            return self.pronunciation[self.i]
        return None

    def parse(self) -> Iterable[Reading]:
        self.i = 0
        while self.i < len(self.pronunciation):
            if ctype(self.next()) is CharacterType.KANJI:
                yield self.grab_reading()
            else:
                self.i += 1

    def grab_reading(self) -> Reading:
        assert ctype(self.next()) is CharacterType.KANJI

        kanji, kana = '', ''

        while ctype(self.next()) is CharacterType.KANJI or self.next() == '々':
            kanji += self.next()
            self.i += 1

        if self.next() != '【':
            # print(f"Warning: kanji {kanji} does not have reading: {self.pronunciation}")
            return Reading(kanji, None)
        self.i += 1

        while self.next() != '】':
            kana += self.next()
            self.i += 1
        self.i += 1

        # if not all(ctype(c) is CharacterType.HIRAGANA for c in kana):
        #     print(f"Warning: not all hiragana: {kana}")

        return Reading(kanji, kana)


Collectible = Union[str, Reading]
Occurrences = dict[Collectible, list[Exercise]]


@dataclass
class ExerciseList:
    exercises: list[Exercise]
    words: bool

    @cached_property
    def ccounts(self) -> dict[CharacterType, Occurrences]:
        out: dict[CharacterType, Occurrences] = {
            ct: {}
            for ct in CharacterType
        }

        for e in self.exercises:
            s = e.string(self.words)
            for c in s:
                ct = ctype(c)
                if c not in out[ct]:
                    out[ct][c] = []
                out[ct][c].append(s)

        return out

    @cached_property
    def ctype_counts(self) -> dict[CharacterType, int]:
        return {
            ct: sum(len(exercises) for exercises in self.ccounts[ct].values())
            for ct in CharacterType
        }

    @cached_property
    def readings(self) -> Occurrences:
        out: dict[Reading, list[Exercise]] = {}

        for e in self.exercises:
            for reading in ReadingsParser(e).parse():
                if reading not in out:
                    out[reading] = []
                out[reading].append(e)

        return out

    @cached_property
    def readings_by_character(self) -> dict[str, list[tuple[Reading, list[Exercise]]]]:
        out: dict[str, list[tuple[Reading, list[Exercise]]]] = {}

        for reading, exercises in self.readings.items():
            for c in reading.kanji:
                if c not in out:
                    out[c] = []
                out[c].append((reading, exercises))

        for l in out.values():
            l.sort(key=lambda x: len(x[1]))

        return out

    @cached_property
    def lemmas(self) -> Occurrences:
        out: Occurrences = {}

        for e in tqdm(self.exercises):
            for t in e.tokens:
                if t.lemma not in out:
                    out[t.lemma] = []
                out[t.lemma].append(e)

        TokenManager.write()

        del out[None]

        return out

    def get_occurrences(self, collection_type: str):
        collection_type = collection_type.upper()

        if collection_type == "LEMMAS":
            return self.lemmas
        elif collection_type == "READINGS":
            return self.readings
        else:
            return self.ccounts[CharacterType[collection_type]]


Readings = dict[str, dict[str, int]]


def add_reading(readings: Readings, kanji: str, reading: str, count: int):
    if kanji not in readings:
        readings[kanji] = {}

    if reading in readings[kanji]:
        raise ValueError(f"Reading already present: {kanji} {reading}")

    readings[kanji][reading] = count


def is_regular_reading(kanji: str, multi_kanji_reading: str, one_kanji_readings: Readings):
    if (kanji == "") is not (multi_kanji_reading == ""):
        print(f"Empty mismatch: {repr(kanji)} {repr(multi_kanji_reading)}")
        return False

    if kanji == "":
        return True

    for logogram in kanji:
        for one_kanji_reading in one_kanji_readings.get(logogram, {}).keys():
            if multi_kanji_reading.startswith(one_kanji_reading):
                if is_regular_reading(kanji[1:], multi_kanji_reading[len(one_kanji_reading):], one_kanji_readings):
                    return True

            if len(one_kanji_reading) > 1 and one_kanji_reading[-1] in "つちくき":
                with_sokuon = one_kanji_reading[:-1] + 'っ'
                if with_sokuon not in one_kanji_readings[logogram] and multi_kanji_reading.startswith(with_sokuon):
                    if is_regular_reading(kanji[1:], multi_kanji_reading[len(with_sokuon):], one_kanji_readings):
                        one_kanji_readings[logogram][with_sokuon] = 0
                        return True

    return False


WIKTIONARY_READINGS_FILE = "wiktionary_readings.json"

WiktionaryReadings: dict[str, dict[str, list[str]]] = {}
if os.path.isfile(WIKTIONARY_READINGS_FILE):
    with open(WIKTIONARY_READINGS_FILE, "r") as fh:
        WiktionaryReadings = json.load(fh)


def wiktionary_readings(c: str) -> dict[str, list[str]]:
    assert len(c) == 1

    if c in WiktionaryReadings:
        return WiktionaryReadings[c]

    section = get_wiktionary_section(c, "Japanese")
    out = {}
    in_readings = False
    for e in section:
        if e.name == "h4" and e.span.text == "Readings":
            in_readings = True

        elif e.name == "ul" and in_readings:
            for li in e.find_all("li"):
                if li.b is None:
                    if not li.attrs.get("class") == ['mw-empty-elt']:
                        print(c)
                    continue

                rs = []
                for reading in li.span.find_all("i", {"class": "Hira mention"}, recursive=False):
                    rs.append(reading.text)
                for joyo in li.span.find_all("mark", {"class": "jouyou-reading"}):
                    rs.append(joyo.i.text)

                for reading in rs:
                    if not all(ctype(kana) is CharacterType.HIRAGANA for kana in reading):
                        print(c, reading)
                        rs.remove(reading)

                out[li.b.text] = rs

            break

    WiktionaryReadings[c] = out
    with open(WIKTIONARY_READINGS_FILE, "w") as fh:
        json.dump(WiktionaryReadings, fh, indent=2, sort_keys=True, ensure_ascii=False)

    return out


CSV_ONSETS_NO_Y = ("", "k", "g", "s", "z", "t", "d", "n", "h", "b", "m", "y", "r", "w")
CSV_ONSETS = []
for o in CSV_ONSETS_NO_Y:
    CSV_ONSETS.append(o)
    if o not in ("", "d", "y", "w"):
        CSV_ONSETS.append(o + "y")


CSV_FINALS = []
for v in "aiueo":
    for end in ("", "ki", "ku", "ti", "tu", "N"):
        CSV_FINALS.append(v + end)
for diphthong in ["ai", "ei", "ou", "uu", "ui"]:
    i = CSV_FINALS.index(diphthong[0])
    CSV_FINALS.insert(i+1, diphthong)


ONSET_RESPELLINGS = {
    "sy": "sh",
    "zy": "j",
    "ty": "ch",
}


def make_readings_csv(title: str, readings: list[str], separator=','):
    pairs = {}

    for reading in readings:
        onset, final = parse_onset(phonemic_transcribe_hiragana(reading))
        if onset not in CSV_ONSETS or final not in CSV_FINALS:
            print(reading, phonemic_transcribe_hiragana(reading))
        else:
            pairs[(onset, final)] = pairs.get((onset, final), 0) + 1

    content = separator.join(['', *[ONSET_RESPELLINGS.get(o, o) for o in CSV_ONSETS]]) + "\n"
    for final in CSV_FINALS:
        content += final.replace("tu", "tsu").replace("ti", "chi").replace("N", "n")
        for onset in CSV_ONSETS:
            content += separator
            if (onset, final) in pairs:
                content += str(pairs[(onset, final)])
        content += '\n'

    os.makedirs('readings', exist_ok=True)
    with open(f"readings/{title}.csv", "w") as fh:
        fh.write(content)


@dataclass
class ReadingsAnalysis:
    el: ExerciseList

    def __post_init__(self):
        self.one_kanji_readings: Readings = {}
        multi_kanji_readings: Readings = {}

        for (kanji, reading), exercises in self.el.readings.items():
            if len(kanji) == 1:
                add_reading(self.one_kanji_readings, kanji, reading, len(exercises))
            else:
                add_reading(multi_kanji_readings, kanji, reading, len(exercises))

        self.regular_multi_kanji_readings: Readings = {}
        self.irregular_multi_kanji_readings: Readings = {}

        for kanji, readings in multi_kanji_readings.items():
            for reading, count in readings.items():
                if is_regular_reading(kanji, reading, self.one_kanji_readings):
                    add_reading(self.regular_multi_kanji_readings, kanji, reading, count)
                else:
                    add_reading(self.irregular_multi_kanji_readings, kanji, reading, count)


def joyo_stats(el: ExerciseList):
    kanji_counts = {
        k: len(exercises)
        for k, exercises in el.ccounts[CharacterType.KANJI].items()
    }
    print(f"{len(kanji_counts)} kanji\n")

    for level in JOYO.keys():
        cumulayive_joyo = load_joyo(level)
        cumulative_included_joyo = [j for j in cumulayive_joyo if j in kanji_counts]
        cumulative_well_tested_joyo = [j for j in cumulayive_joyo if (kanji_counts.get(j, 0) >= WELL_TESTING_THRESHOLD)]

        print(f"{len(cumulative_well_tested_joyo)}/{len(cumulayive_joyo)} Joyo up to level {level} are well-tested")
        print(f"{len(cumulative_included_joyo)}/{len(cumulayive_joyo)} Joyo up to level {level} are tested")

        level_included_joyo = [j for j in JOYO[level] if j in kanji_counts]
        level_well_tested_joyo = sorted([j for j in JOYO[level] if kanji_counts.get(j, 0) >= WELL_TESTING_THRESHOLD])
        level_poorly_tested_joyo = sorted(list(set(level_included_joyo) - set(level_well_tested_joyo)))
        level_excluded_joyo = sorted([j for j in JOYO[level] if j not in kanji_counts])

        if len(level_well_tested_joyo) > 0:
            print(f"{len(level_well_tested_joyo)} well tested joyo: {''.join(level_well_tested_joyo)}")
        if len(level_poorly_tested_joyo) > 0:
            print(f"{len(level_poorly_tested_joyo)} poorly tested joyo: {''.join(level_poorly_tested_joyo)}")
        if len(level_excluded_joyo) > 0:
            print(f"{len(level_excluded_joyo)} excluded Joyo: {''.join(level_excluded_joyo)}")

        print()


def print_ctype_counts(el: ExerciseList):
    for t, n in sorted(list(el.ctype_counts.items()), key=lambda x: x[1]):
        print(f"{t.value:<20} {n:>6}")


def export_frequencies(el: ExerciseList):
    dirname = f'frequency/jpn-eng'
    os.makedirs(dirname, exist_ok=True)
    for ct in CharacterType:
        with open(os.path.join(dirname, f'{ct.value}.txt'), 'w') as fh:
            for w, f in sorted(list(el.ccounts[ct].items()), key=lambda x: x[1], reverse=True):
                fh.write(f"{w}\t{f}\n")


def print_most_common(el: ExerciseList, collection_type: str, limit: str = '100'):
    occurrences = sorted(
        el.get_occurrences(collection_type).items(),
        key=lambda x: len(x[1]),
    )
    limit = min(int(limit), len(occurrences))

    for i, (collectible, exercises) in enumerate(occurrences[-limit:]):
        print(f"{limit - i:>4} {len(exercises):>4} {collectible}")

    print(f"{len(occurrences)} total {collection_type} ({len(occurrences)/len(el.exercises):.2f} per exercise)")

    well_tested = [
        (o, exercises)
        for o, exercises in occurrences
        if len(exercises) >= WELL_TESTING_THRESHOLD
    ]
    print(f"{len(well_tested)} well-tested {collection_type} ({len(well_tested)/len(el.exercises):.2f} per exercise)")


def run_survey(ctype: CharacterType, chars: list[str], sample: int = 1):
    tested = 0
    known = 0
    wrong: list[str] = []

    for i in range(0, len(chars), sample or 1):
        character = chars[i]
        print(character, end='')

        if ctype in TRANSCRIPTIONS:
            input()
            print(TRANSCRIPTIONS[ctype][character])
        else:
            print()

        response = input('Known? (y for yes) ')
        print()

        tested += 1
        if response == 'y':
            known += 1
        else:
            wrong.append(character)

    print(f"{known}/{tested} known ({round(100 * known / tested, 1)}%)")

    if sample == 0 and len(wrong) > 0:
        print()
        run_survey(ctype, wrong, 0)


def survey(el: ExerciseList, ctype: str, limit: str = '100', sample: str = '1'):
    ctype = CharacterType[ctype.upper()]

    most_common = [
        c for c, count in sorted(
            el.ccounts[ctype].items(),
            key=lambda x: x[1],
            reverse=True,
        )
    ]

    run_survey(ctype, most_common[:int(limit)], int(sample))


NORMAL_CTYPES = (CharacterType.KANJI, CharacterType.HIRAGANA, CharacterType.KATAKANA, CharacterType.SPECIAL)


def print_nonstandard(el: ExerciseList):
    for e in el.exercises:
        s = e.string(el.words)
        nonstandard = [c for c in s if ctype(c) not in NORMAL_CTYPES]
        if nonstandard:
            print(s)
            print(','.join(nonstandard))
            print()


def reading_analysis(el: ExerciseList, limit: str = '100'):
    analysis = ReadingsAnalysis(el)
    limit = int(limit)

    for name, multi_kanji_readings in (("Regular", analysis.regular_multi_kanji_readings),
                                       ("Irregular", analysis.irregular_multi_kanji_readings)):
        print(f"{name} readings:\n")

        multi_kanji_readings = [
            (kanji, reading, count)
            for kanji, readings in multi_kanji_readings.items()
            for reading, count in readings.items()
        ]
        multi_kanji_readings.sort(key=lambda x: x[2])
        list_limit = min(limit, len(multi_kanji_readings))

        for i, (kanji, reading, count) in enumerate(multi_kanji_readings[-list_limit:]):
            print(f"{list_limit-i:>4} {kanji:＿<4} {reading:＿<6} {count:>4}")
            for logogram in kanji:
                print(f"     - {logogram} {'/'.join(analysis.one_kanji_readings.get(logogram, {}).keys())}")

        print(f"\n{len(multi_kanji_readings)} {name.lower()} readings.\n")


def containing(el: ExerciseList, substring: str, limit: str = '100'):
    for e in el.exercises:
        s = e.string(el.words)
        if substring in s:
            print(e.text)
            print(e.pronunciation)
            print(e.tokens)
            print(e.translation)
            print()


LATEX_TEMPLATE = r"""
\documentclass{article}
\usepackage{CJKutf8}

\title{Most common Kanji in Clozemaster}
\date{}

\setlength\parindent{24pt}

\begin{document}

\maketitle

%s

\end{document}
"""


CJK_FONT = "min"


def latex(el: ExerciseList):
    most_common_kanji = sorted(
        el.ccounts[CharacterType.KANJI].items(),
        key=lambda x: x[1],
        reverse=True,
    )

    content = ""

    for character, count in most_common_kanji:
        content += (
            f"\\begin{{CJK}}{{UTF8}}{{{CJK_FONT}}}"
            f"\\section{{{character}}}"
            "\\end{CJK}\n\n"
            f"{count} occurrences\n\n"
            "\\bigskip\n\n"
        )

        for reading, exercises in el.readings_by_character[character][::-1]:
            content += (
                f"\\noindent \\begin{{CJK}}{{UTF8}}{{{CJK_FONT}}}"
                f"{reading.kanji}　【{reading.kana}】"
                "\\end{CJK}\n"
                f"{len(exercises)} occurrence{'s' if len(exercises) > 1 else ''}\n\n"
                "\\bigskip\n\n"
            )

            exercise = exercises[0]

            content += (
                f"\\begin{{CJK}}{{UTF8}}{{{CJK_FONT}}}"
                f"{exercise.pronunciation}"
                "\\end{CJK}\n\n"
                f"{exercise.translation}\n\n"
                "\\bigskip\n\n"
            )

    print(LATEX_TEMPLATE % content)


def played_pattern(el: ExerciseList):
    for i, e in enumerate(el.exercises):
        print('_' if e.numPlayed == 0 else '#', end='')
        if i % 60 == 59:
            print()

    print()


def to_play_histogram(el: ExerciseList):
    current_counts = {}
    for e in el.exercises:
        if e.numPlayed == 0:
            continue
        for t in e.tokens:
            current_counts[t.lemma] = current_counts.get(t.lemma, 0) + 1
    del current_counts[None]

    total_counts = {}
    for e in el.exercises:
        for t in e.tokens:
            total_counts[t.lemma] = total_counts.get(t.lemma, 0) + 1
    del total_counts[None]

    played_total_counts = sorted(
        [(l, total_counts[l]) for l in current_counts.keys()],
        key=lambda x: x[1],
    )

    cap = 100
    for lemma, count in played_total_counts:
        print(f"{lemma:＿<6} {'#'*min(count, cap)}{str(count) if count > cap else ''}")

    print(f"{len([l for l, c in current_counts.items() if c >= WELL_TESTING_THRESHOLD])}"
          f"/{len(current_counts)} currently well-tested")
    print(f"{len([l for l in current_counts.keys() if total_counts[l] >= WELL_TESTING_THRESHOLD])}"
          f"/{len(current_counts)} eventually well-tested")


def all_wiktionary_readings(el: ExerciseList):
    kanji = set()

    for e in el.exercises:
        for c in e.sentence:
            if ctype(c) is CharacterType.KANJI:
                kanji.add(c)

    for c in load_joyo(7):
        kanji.add(c)

    readings_by_type = {}
    for c in tqdm(list(kanji)):
        for reading_type, readings in wiktionary_readings(c).items():
            if reading_type not in readings_by_type:
                readings_by_type[reading_type] = []

            readings_by_type[reading_type] += readings

    for rt in sorted(list(readings_by_type.keys()), key=lambda t: -len(readings_by_type[t])):
        print(rt)

        readings = readings_by_type[rt]

        print(f"{len(readings)} readings")
        print(f"{len(set(readings))} distinct readings")

        if rt.endswith("-on"):
            make_readings_csv(rt, readings)

        print()


def coverage(el: ExerciseList, ctype: str):
    all_el = ExerciseList(all_exercises("jpn-eng"), words=el.words)

    occurrences = el.get_occurrences(collection_type=ctype)
    all_occurrences = all_el.get_occurrences(collection_type=ctype)

    seen_items = set(occurrences.keys())
    well_tested_items = set(item for item, exercises in occurrences.items() if len(exercises) >= WELL_TESTING_THRESHOLD)

    for title, item_set in (('tested', seen_items), ('well-tested', well_tested_items)):
        total_occurrences = 0
        occurrence_coverage = 0

        for item, exercises in all_occurrences.items():
            total_occurrences += len(exercises)
            if item in item_set:
                occurrence_coverage += len(exercises)

        print(f"{occurrence_coverage}/{total_occurrences} ({100*occurrence_coverage/total_occurrences:<.1f}%)"
              f" {ctype} usages are among {title} items.")


def reload_sentences(_: ExerciseList):
    exercises = all_exercises('jpn-eng', force_reload=True)
    print(f"{len(exercises)} sentences downloaded.")


DISPATCH_TABLE: dict[str, Callable[[ExerciseList, ...], None]] = {
    'reload': reload_sentences,
    'joyo': joyo_stats,
    'ctypes': print_ctype_counts,
    'nonstandard': print_nonstandard,
    'export': export_frequencies,
    'common': print_most_common,
    'reading_analysis': reading_analysis,
    'survey': survey,
    'latex': latex,
    'contain': containing,
    'played': played_pattern,
    'to_play': to_play_histogram,
    "wiktionary_readings": all_wiktionary_readings,
    "coverage": coverage,
}


def run_command(command: str, words: bool, playing: bool, num_sentences: Optional[int], args: list[str]):
    exercises = all_exercises("jpn-eng")
    if playing:
        exercises = [
            e for e in exercises
            if e.numPlayed > 0
        ]
    elif num_sentences:
        exercises = exercises[:num_sentences]

    el = ExerciseList(exercises, words)

    if command in DISPATCH_TABLE:
        DISPATCH_TABLE[command](el, *args)
    else:
        raise ValueError(f"Invalid command: {command} (valid commands: {', '.join(DISPATCH_TABLE.keys())})")


parser = argparse.ArgumentParser()
parser.add_argument('-w', '--words', action='store_true', help='Use cloze words instead of entire sentences')
parser.add_argument('-p', '--playing', action='store_true', help='Limit to sentences which I am playing')
parser.add_argument('-n', '--num_sentences', type=int, default=None, required=False, help='Number of sentences')
parser.add_argument('command', type=str, choices=list(DISPATCH_TABLE.keys()))
parser.add_argument('args', type=str, nargs='*')


if __name__ == "__main__":
    args = parser.parse_args()
    run_command(command=args.command, words=args.words, playing=args.playing, num_sentences=args.num_sentences,
                args=args.args)
