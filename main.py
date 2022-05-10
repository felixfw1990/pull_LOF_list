# -*- coding: UTF-8 -*-
from urllib import request
from bs4 import BeautifulSoup
import time
import json
import re
import xlwt


# -----------------------------------------------------------------------
# run
# -----------------------------------------------------------------------
def run(search_str, o_type):
    search_str = request.quote(search_str.encode('utf-8'))
    code_datas = search_list(search_str)
    file_name = request.unquote(search_str)
    count_da = str(len(code_datas))

    datas = []

    print("共计"+count_da+"条")

    index = 1
    for code_data in code_datas:
        print("抓取第"+str(index)+"条")
        datas.append(output(code_data))
        index = index+1

    if o_type == 'md':
        save_md(file_name, datas)
    else:
        save_ex(file_name, datas)


# -----------------------------------------------------------------------
# 存储到md
# -----------------------------------------------------------------------
def save_md(search_name, datas):

    part = [
        "---", "---", "---", "---", "---",
        "---", "---", "---", "---", "---",
        "---", "---", "---", "---"
    ]
    header = [
        "代码",  "类型",  "成立时间",  "买入费率",  "管理费率",  "托管费率", "销售费率",
        "股票占有率",  "经理持有总基金数",  "基金总资金", "基金经理持有总资金", "名称",
        "投资目标",  "交易状态"
    ]

    datas.insert(0, part)
    datas.insert(0, header)

    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    file_name = search_name+now_time+".md"
    file_model = open(file_name, 'x')

    print(datas)
    for data in datas:
        temp = "|"
        for v in data:
            temp = temp + v + "|"
        temp = temp + "\n"
        file_model.write(temp)

    file_model.close()


# -----------------------------------------------------------------------
# 存储到电子表格
# -----------------------------------------------------------------------
def save_ex(search_name, datas):

    title = [
        "代码", "类型", "成立时间", "买入费率", "管理费率", "托管费率", "销售费率",
        "股票占有率", "经理持有总基金数", "基金总资金", "基金经理持有总资金", "名称",
        "投资目标", "交易状态"
    ]
    datas.insert(0, title)

    ex = xlwt.Workbook()
    sheet = ex.add_sheet('case1_sheet')

    row = 0
    for data in datas:
        col = 0
        for v in data:
            sheet.write(row, col, v)
            col += 1
        row += 1

    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    file_name = search_name+now_time+".xls"

    ex.save(file_name)


# -----------------------------------------------------------------------
# 单条数据拼接
# -----------------------------------------------------------------------
def output(code_data):
    home_url = "http://fund.eastmoney.com/"+code_data['code']+".html"
    rate_url = "http://fundf10.eastmoney.com/jjfl_"+code_data['code']+".html"
    conf_url = "http://fundf10.eastmoney.com/zcpz_"+code_data['code']+".html"
    info_url = "http://fundf10.eastmoney.com/jbgk_"+code_data['code']+".html"

    home_soup = get_soup(home_url)
    rate_soup = get_soup(rate_url)
    conf_soup = get_soup(conf_url)
    info_soup = get_soup(info_url)

    code = code_data['code']  # 代码
    info = get_info(info_soup)  # 投资目标
    sale = get_sale(rate_soup)  # 销售费率
    name = code_data['name']  # 名称
    money = get_money(home_soup)  # 基金总资金
    insert = get_insert(home_soup)  # 买入费率
    manager = get_manager(rate_soup)  # 管理费率
    the_type = get_type(code_data['name'])  # 类型
    parallel = get_parallel(home_soup)  # 经理持有总基金数
    birth_day = get_birth_day(home_soup)  # 成立时间
    get_status = get_get_status(home_soup)  # 交易状态
    collocation = get_collocation(rate_soup)  # 托管费率
    stock_shared = get_stock_shared(conf_soup)  # 股票占有率
    manage_money = get_manage_money(home_soup)  # 基金经理持有总资金

    return [
        code, the_type, birth_day, insert, manager, collocation,
        sale, stock_shared, parallel, money, manage_money, name,
        info, get_status
    ]


# -----------------------------------------------------------------------
# 获取列表
# -----------------------------------------------------------------------
def search_list(search_str):
    try:
        base_url = "http://fundsuggest.eastmoney.com/FundSearch/api/FundSearchPageAPI.ashx"
        url = base_url+"?m=1&key="+search_str+"&pageindex=0&pagesize=1000"
        soup = get_soup(url)

        json_str = soup.html.body.p.string
        result = json.loads(json_str)
        result = result['Datas']

        out_put = []

        for data in result:
            out_put.append({'code': data['CODE'], 'name': data['NAME']})

        return out_put
    except Exception as e:
        return '异常'


# -----------------------------------------------------------------------
# 获取投资类型  增强 指数
# -----------------------------------------------------------------------
def get_type(name):
    z_index = name.find('增强')
    f_index = name.find('分级')
    e_index = name.find('ETF')

    if z_index > -1:
        return '增强'
    elif f_index > -1:
        return '分级'
    elif e_index > -1:
        return 'ETF'
    return '指数'


# -----------------------------------------------------------------------
# 获取成立时间
# -----------------------------------------------------------------------
def get_birth_day(soup):
    try:
        # info
        info = soup.find('div', class_="infoOfFund")
        birth_day = info.table.contents[1].td.get_text()
        birth_day = birth_day[6:]
        birth_day = time.strftime("%Y%m%d", time.strptime(birth_day, "%Y-%m-%d"))

        return birth_day
    except Exception as e:
        return time.strftime("%Y%m%d%H%M%S", time.localtime())


# -----------------------------------------------------------------------
# 获取买入费率
# -----------------------------------------------------------------------
def get_insert(soup):
    try:
        info = soup.find('span', class_="nowPrice")
        number = info.get_text()
        return number
    except Exception as e:
        return '9.99%'


# -----------------------------------------------------------------------
# 获取管理费率
# -----------------------------------------------------------------------
def get_manager(soup):
    try:
        info = soup.find('div', class_="txt_cont")
        text = info.div.contents[4].div.table.tr.contents[1].get_text()
        text = str(text)
        text = text[0:5]
        return text
    except Exception as e:
        return '9.99%'


# -----------------------------------------------------------------------
# 获取托管费率
# -----------------------------------------------------------------------
def get_collocation(soup):
    try:
        info = soup.find('div', class_="txt_cont")
        text = info.div.contents[4].div.table.tr.contents[3].get_text()
        text = str(text)
        text = text[0:5]
        return text
    except Exception as e:
        return '9.99%'


# -----------------------------------------------------------------------
# 获取销售费率
# -----------------------------------------------------------------------
def get_sale(soup):
    try:
        info = soup.find('div', class_="txt_cont")
        info = info.div.contents[4].div.table.tr.contents[5].get_text()
        info = re.findall(r"\d*\.\d+%|\d+%", info, re.M)
        return info[0]
    except Exception as e:
        return '9.99%'


# -----------------------------------------------------------------------
# 获取股票净占比例
# -----------------------------------------------------------------------
def get_stock_shared(soup):
    try:
        info = soup.find('div', class_="detail")
        text = info.find('div', class_='txt_cont')
        text = text.div.find('div', class_='nb')
        text = text.div.table.tbody.tr.contents[1].get_text()
        return text
    except Exception as e:
        return '0.00%'


# -----------------------------------------------------------------------
# 获取基金经理持有总基金数量
# -----------------------------------------------------------------------
def get_parallel(soup):
    try:
        info = soup.find('div', id="fundManager")
        info = info.find('tr', class_='noBorder')
        url = info.find('td', class_='td02').a['href']

        info = get_soup(url)
        info = info.find('div', class_='content_out').contents[1].table.tbody
        info = info.find_all('tr')
        info = len(info)
        info = str(info)
        return info
    except Exception as e:
        return '1000'


# -----------------------------------------------------------------------
# 获取基金总资金
# -----------------------------------------------------------------------
def get_money(soup):
    try:
        info = soup.find('div', class_="infoOfFund")
        info = info.table.tr.contents[1].get_text()
        info = re.findall(r"\d*\.\d+|\d+", info, re.M)

        return info[0]
    except Exception as e:
        return '0'


# -----------------------------------------------------------------------
# 获取基金经理持有总资金
# -----------------------------------------------------------------------
def get_manage_money(soup):
    try:
        info = soup.find('div', id="fundManager")
        info = info.find('tr', class_='noBorder')
        url = info.find('td', class_='td02').a['href']

        info = get_soup(url)
        info = info.find('div', class_='gmContainer')
        info = info.div.find('span', class_='numtext').get_text()
        info = re.findall(r"\d*\.\d+|\d+", info, re.M)

        return info[0]
    except Exception as e:
        return '0'


# -----------------------------------------------------------------------
# 获取基金投资目标
# -----------------------------------------------------------------------
def get_info(soup):
    try:
        info = soup.find('div', class_="txt_in").find('div', class_='boxitem')
        info = info.p.get_text()
        info = info.strip().replace(' ', '')
        info = re.findall(r"\d*\.\d+%|\d+%", info, re.M)
        out_put = ''

        for i in info:
            out_put = out_put+i+"-"

        if len(out_put) > 0:
            out_put = out_put[0:-1]

        return out_put
    except Exception as e:
        return '异常'


# -----------------------------------------------------------------------
# 获取交易状态
# -----------------------------------------------------------------------
def get_get_status(soup):
    try:
        info = soup.find('div', class_="buyWayStatic").find('span', class_='staticCell').get_text()
        info = info.strip().replace(' ', '')
        return info
    except Exception as e:
        return '异常'


# -----------------------------------------------------------------------
# 获取html对象
# -----------------------------------------------------------------------
def get_soup(url):
    try:
        response = request.urlopen(url)
        html = response.read()
        html = html.decode("utf-8")
        soup = BeautifulSoup(html, "lxml")
        return soup
    except Exception as e:
        return '异常'


# -----------------------------------------------------------------------
# run
# -----------------------------------------------------------------------
if __name__ == '__main__':
    print("此文件以天天基金网数据为基础\n")
    print('请输入关键字,比如:中证500指数:')
    strs = input()
    print('请输入导出格式ex|md:')
    out_type = input()
    run(strs, out_type)  # ex|md

