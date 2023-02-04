from dataclasses import dataclass
import json
import os
from typing import Iterable, Optional

from bs4 import BeautifulSoup as bs
import requests

from shared.lib.networking import get_wiktionary_section
from shared.lib.dataclasses import Exercise
from .ctypes import CharacterType, ctype
from .kana import romaji_to_hiragana, match_conforming


def load_wikipedia_joyo():
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


def joyo_up_to(max_level=6) -> set[str]:
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
        ideographic_space = '\u3000'
        return f"{self.kanji.ljust(2, ideographic_space)}【{self.kana}】"

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
            return Reading(kanji, None)
        self.i += 1

        while self.next() != '】':
            kana += self.next()
            self.i += 1
        self.i += 1

        return Reading(kanji, kana)


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
                        print(f"Unexpected li: {c}")
                    continue

                reading_elems = []
                for reading in li.span.find_all("i", {"class": "Hira mention"}, recursive=False):
                    reading_elems.append(reading)
                for joyo in li.span.find_all("mark", {"class": "jouyou-reading"}):
                    reading_elems.append(joyo.i)

                rs = []
                for kana_reading in reading_elems:
                    romaji_reading = kana_reading
                    while romaji_reading is not None:
                        if ((getattr(romaji_reading, "attrs", None) is not None) and
                                (romaji_reading.attrs.get("class", None) == ["mention-tr", "tr"])):
                            break

                        romaji_reading = romaji_reading.next_sibling

                    if romaji_reading is None:
                        print(f"Malformed Wiktionary page for {c}: {romaji_reading}")
                        continue

                    if romaji_reading.u is None:
                        reading = kana_reading.text
                    else:
                        reading = romaji_to_hiragana(romaji_reading.u.text)
                        reading, matches = match_conforming(reading, kana_reading.text)
                        if not matches:
                            raise ValueError(f"Mismatched hiragana: {kana_reading.text} {reading} {romaji_reading.u}")

                    if not all(ctype(kana) is CharacterType.HIRAGANA for kana in reading):
                        print("Non-hiragana in reading:", c, reading)

                    elif reading not in rs:
                        rs.append(reading)

                out[li.b.text] = rs

            break

    WiktionaryReadings[c] = out
    with open(WIKTIONARY_READINGS_FILE, "w") as fh:
        json.dump(WiktionaryReadings, fh, indent=2, sort_keys=True, ensure_ascii=False)

    return out
