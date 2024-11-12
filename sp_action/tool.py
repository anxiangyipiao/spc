import re
from lxml import etree
from readability import Document

keyword_types = {
    '油变': ["油变", "油浸", "35KV", "220KV", "66KV"],
    '干变': ["干式变压器", "干式配电变压器", "干式电力变压器", "scb", "sclb", "sczb", "zsc"],
    '成套': ["KYN61", "KYN28", "XGN15", "GGD", "GCS", "MNS", "YB口", "ZGS22", "JXF", "中性点", "整流变", "箱变", "华变",
             "欧变", "美变", "双分裂变压器", "分裂变", "变流变"]
}
keywords = ["油变", "油浸", "10KV", "35KV", "220KV", "落后产能淘汰", "主变", "中性点", "整流变", "配电变压器",
            "低压变压器", "高压变压器", "配变", "配电变压器", "电力变压器", "变压器", "厂用变", "66KV", "变压器",
            "变电站", "调压变压器", "节能变压器", "箱变", "华变", "欧变", "美变", "双分裂变压器", "分裂变", "变流变",
            "干式变压器", "干式配电变压器", "干式电力变压器",
            "scb", "sclb", "sczb", "zsc", "KYN61", "KYN28", "XGN15",
            "GGD", "GCS", "MNS", "YB口", "ZGS22", "JXF"
            ]

invalidKeywords = ["中标", "成交", "候选人", "结果", "招标失败", "采购失败", "环境影响", "环评", "废标", "流标", "评标",
                   "开标", "入围", "监理", "水土保持", "竣工", "勘察设计", "工程勘察", "验收", "备案", "审计", "审批",
                   "评审", "核准", "受理", "批复", "地质灾害", "灾害危险性评估", "可研性", "可研初设", "可研设计",
                   "可行性研究", "可行性报告", "预防性试验", "预防性检测", "预防性测试", "完成公示", "中止公告",
                   "终止公告", "终止招标", "中选公告", "失败公告", "终止", "编制", "开标记录", "设计服务", "技术服务",
                   "安全评估", "安全评价", "安全防护", "影响评价", "可研报告", "维护检修", "外委维护", "检修维护",
                   "运行维护", "运维", "维保", "维修", "代维", "变压器处置", "挂牌", "转让", "拍卖", "变卖", "竞拍",
                   "出让", "招租", "医疗设备", "出租", "零星物资", "结算", "保险", "保洁", "劳保", "劳务分包",
                   "劳务外包", "劳务招标", "外包项目", "服务外包", "施工专业承包", "消缺工程", "工程分包",
                   "工程专业分包", "工程咨询", "工程造价咨询", "工程招标代理", "工程采购公示", "改造设计", "改造施工",
                   "施工材料", "标识", "批前公示", "零星材料", "评审公示", "评价报告", "社会稳定风险评估",
                   "水土保持报告", "影响评估", "泰开", "成套公司", "送变电公司SD", "电力电子公司HD", "物业管理", "监控",
                   "电梯", "路灯专用", "灯具", "刀具", "夹具", "金具", "工具", "锁具", "家具", "五金", "消防物资",
                   "配件", "附件", "硬件", "辅材", "耗材", "管材", "资产评估", "风险评估", "废旧物资处置", "无功补偿",
                   "补偿装置", "补偿设备", "预算审核", "采购与安装", "采购及安装", "办公用品", "异常公告", "处置公告",
                   "评标报告", "在线监测", "在线温度监测", "监测项目", "监测装置", "监测系统", "非物资", "风机塔筒",
                   "医用", "体检", "射线", "导线", "装修", "工程类", "服务类", "迁改工程", "送出工程", "拆除工程",
                   "电缆工程", "隔离开关", "赛迪集团", "开滦集团", "内燃柴电机组", "灭火物资", "灭火系统", "灭火装置",
                   "防火材料", "防火物资", "防火槽盒", "碎石机", "交换机", "电动机", "输送机", "起重机", "空气压缩机",
                   "围栏", "护栏", "壳体类", "塔筒", "绝缘件", "绝缘鞋", "绝缘子", "绝缘垫", "绝缘手套", "绝缘胶垫",
                   "绝缘材料", "接地材料", "工程材料", "装置性材料", "防护材料", "消耗性材料", "地脚螺栓", "方案设计",
                   "专项设计", "冷却风扇", "防雷技术", "管道建设", "保护柜", "保护屏", "保护定值", "生产物资",
                   "报废物资", "废旧物资", "废旧设备", "报废资产", "资产处置", "报废设备", "经营权采购", "平台采购",
                   "图书采购", "车辆采购", "食品采购", "安装采购", "试验采购", "风机采购", "性能试验", "仪器设备",
                   "仪器仪表", "仪表物资", "教学设备", "教学仪器", "教室设备", "信息系统", "信息化建设", "油光谱",
                   "消弧线圈", "热缩头", "电缆头", "电缆桥", "电缆终端", "电缆槽盒", "交流电缆", "直流电缆", "安全稳定",
                   "安全阀", "安全预警系统", "安防系统", "防雷", "化学药品", "污水处理", "污水治理", "尾水治理",
                   "废水处理", "故障处理", "设备处理", "镀锌型", "实训室", "花岗岩", "试验及调试", "配电板", "通信器材",
                   "围墙整治", "高爆柜", "照明配电箱", "研发与应用", "研究与应用", "研究及应用", "显微镜", "化工制品",
                   "石灰石", "定值计算", "数字化集成", "环境整治", "可视化平台", "吸音板", "预试", "接线板", "定值核算",
                   "测绘", "接地箱", "接地桩", "委托运行", "伸缩门", "截止阀", "支架", "除湿", "导地线", "避雷针",
                   "补遗", "热熔", "机械使用费", "基础桩", "邀请函", "邀请招标", "渗油", "实训器材", "验收公告",
                   "绝缘板", "挂出", "调速系统", "水泥制品", "供暖系统", "标示牌", "智能信息化", "招标计划", "控制主板",
                   "打捆项目", "安全检测", "灭火器", "安全设备", "驱鸟器", "LED", "灯箱", "铝板", "经营权", "广东电网",
                   "广西电网", "云南电网", "海南电网", "继电保护", "泡沫剂", "土地使用权", "传感器", "桥架", "答疑",
                   "劳务", "维护服务", "检测", "巡查", "变压器油", "质量检测", "维护", "故障", "保养", "答疑", "中标",
                   "电压互感器", "小箱变事业部", "大箱变事业部", "变压器事业部", "建设工程", "隔离变", "迁移", "修理",
                   "维修", "迁改", "医疗器械", "服务公开招标", "服务招标", "设计项目", "澄清", "招标代理", "更正公告",
                   "检修", "主变油", "变压器油", "变更公告", "中选人", "干式变压器", "开关柜事业部", "小箱变事业部",
                   "大箱变事业部", "采购清单( 整流变 在正文中 )", "变压器事业部", "总包", "屋顶", "施工", "物资",
                   "检测", "巡查", "变压器油", "质量检测", "维护", "材料", "故障", "保养", "答疑", "中标", "改造",
                   "电压互感器", "电缆", "小箱变事业部", "大箱变事业部", "变压器事业部", "建设工程", "隔离变", "迁移",
                   "修理", "维修", "迁改", "安装工程", "医疗器械", "服务公开招标", "服务招标", "设计项目", "澄清",
                   "招标代理", "更正公告", "检修", "主变油", "变压器油", "安装工程", "变更公告", "中选人", "批复公告",
                   "备案", "赋码"]


def find_key_by_value(value):
    # 遍历字典，查找键
    for key, values in keyword_types.items():
        if value in values:
            return key
    # 如果没有找到对应的键，则返回None
    return None


def format_html(_html_content):  # 优化html文本显示
    _html_content = re.sub(r'<scripx[\s\S]*?</scripx>', r'', _html_content)
    _html_content = re.sub(r'<scripx[\s\S]*?</scripx>', r'', str(_html_content))
    _html_content = re.sub(u'<scripx[\s\S]*?</scripx>', u'', str(_html_content))  # (,\d+){1,5}<scripx>
    _html_content = re.sub(r'<style[\s\S]*?</style>', r'', str(_html_content))
    _html_content = re.sub(r'\d+\.\d+%', r'', _html_content)
    _html_content = re.sub(r'\r\n', r'\n', _html_content)
    _html_content = re.sub('<h\d>', '<h4>', _html_content)
    _html_content = re.sub('<h\d  ', '<h4  ', _html_content)
    _html_content = re.sub('</h\d>', '</h4>', _html_content)
    _html_content = re.sub(r'MARGIN-RIGHT:  \d*\.?\d+pt', r'MARGIN-RIGHT:  2px;', str(_html_content))
    _html_content = re.sub(r'MARGIN-RIGHT:  \d*\.?\d+px', r'MARGIN-RIGHT:  2px;', str(_html_content))
    _html_content = re.sub(r'MARGIN-LEFT:  \d*\.?\d+pt', r'MARGIN-LEFT:  2px;', str(_html_content))
    _html_content = re.sub(r'MARGIN-LEFT:  \d*\.?\d+px', r'MARGIN-LEFT:  2px;', str(_html_content))
    _html_content = re.sub(r'margin-right:  \d*\.?\d+pt', r'MARGIN-RIGHT:  2px;', str(_html_content))
    _html_content = re.sub(r'margin-right:  \d*\.?\d+px', r'MARGIN-RIGHT:  2px;', str(_html_content))
    _html_content = re.sub(r'margin-left:  \d*\.?\d+pt', r'MARGIN-LEFT:  2px;', str(_html_content))
    _html_content = re.sub(r'margin-left:  \d*\.?\d+px', r'MARGIN-LEFT:  2px;', str(_html_content))
    _html_content = re.sub(r'\n+', r'\n', _html_content)
    _html_content = re.sub(r'\s+', r'  ', _html_content)
    _html_content = re.sub(r'\r{2,100}', r'', _html_content)
    _html_content = re.sub(r'\n{2,100}', r'', _html_content)
    _html_content = str(_html_content).replace("pt", "px")
    _html_content = re.sub(r'FONT-SIZE:  \d*\.?\d+px', r'FONT-SIZE:  9.5pt', _html_content, re.I)
    _html_content = re.sub(r'font-size:  \d*\.?\d+px', r'FONT-SIZE:  9.5pt', _html_content)
    _html_content = re.sub(r'MARGIN: .*?;', r'', _html_content)
    head = '''
        <head>
            <meta name="viewport"
                content="width=device-width,initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no" />
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        </head>
    '''
    _html_content = str(head + _html_content)
    if _html_content.count('<table'):
        text_ = etree.HTML(_html_content)
        _len = len(text_.xpath('//table/tr[0]/td'))
        if _len == 0:
            _len = 1
        i_num = int(100 / _len)
        _html_content = str(_html_content).replace("pt", "px").replace('&amp;nbsp', '')
        _html_content = re.sub(r'WIDTH:  \d+px', '', _html_content)
        _html_content = re.sub(r'width:  \d+px', '', _html_content)
        _html_content = re.sub(r'FONT-SIZE:  \d*\.?\d+px', r'FONT-SIZE:  9.5pt', _html_content, re.I)
        _re = 'width="**********%"'.replace('**********', str(i_num))
        _html_content = re.sub(r'width="\d+"', _re, _html_content)
    _html_content = '<div  style="font-family:  微软雅黑;color:#8B7D7B;FONT-SIZE:  9.5pt;line-height:22px;">  ' + str(
        _html_content) + '</div>'
    return _html_content


def parse_html(html_title,html_content):
    doc = Document(html_content)
    content = doc.summary()

    title = doc.short_title()
    if content and title:
        text = title + content
    else:
        text = title + html_content
    text = html_title + text

    keys = set()
    types = set()

    # if any(invalidKey.lower() in text.lower() for invalidKey in invalidKeywords):
    #     pass
    # else:
    for key in keywords:
        if key.lower() not in text.lower():
            continue
        else:
            keys.add(key)
            info_type = find_key_by_value(key)
            types.add(info_type if info_type else '变压器')
            print(f'存在关键字：{key}类型为：{types}')
    if types:
        return ','.join(map(str, types))
