from django.shortcuts import render
from django.http import HttpResponse
from .models import Vendor, TodoList, UserList, LoginLog
from django.db import connection
from .form import UserForm, LoginForm, TodoForm, TodoForm1, LoginForm1, ChForm, TodoForm2, Cap, HwForm
from django.template.defaulttags import register
from django.contrib import messages
import datetime
from django.contrib.auth.hashers import make_password
#from ipware import get_client_ip
from jinja2 import Environment, FileSystemLoader
from pyecharts.globals import CurrentConfig
CurrentConfig.GLOBAL_ENV = Environment(loader=FileSystemLoader("/var/www/html/Test/myproject/templates"))
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie
from datetime import date, timedelta
from pyecharts.globals import ThemeType
from random import randint
import openpyxl
from pyexcel_ods import save_data
from collections import OrderedDict
from docx import Document
from docx.shared import Inches
from odf.opendocument import OpenDocumentText
from odf.text import P
cursor = connection.cursor()
golden_key = "abc" # 加密金鑰

def Test(request) :
    return render(request, "Test2.html")

def LetterFormat(passward) : # 密碼格式
    lower = False # 需有小寫英文，先設無
    capital = False # 需有大寫英文，先設無
    for letter in passward :
        if letter.isupper() : # 有大寫字母
            capital = True
        if letter.islower() : # 有小寫字母
            lower = True
    if lower and capital : # 有大寫和小寫
        if len(passward) >= 8 : # 長度需>=8
            return 1 # 符合格式
        return 0 # 有大小寫，但長度不對
    return -1 # 沒大小寫

def RevisedMonth(revised_date) : # 從 revised_date 中取得月份
    month = ""
    for i in range(len(revised_date)) :
        if revised_date[i] == "-" : # 遇到 - 就把月份加起來
            month = revised_date[i+1]
            if revised_date[i+2] != "-" : # 如果是兩位數的月份
                month = month + revised_date[i+2]
            return int(month)
    return int(month)

def CheckRevised(today, revised_date) : # 檢查是否過3個月沒更改密碼
    today_month = today.month
    if today.year > int(revised_date[:4]) : # 登入的年分大於三個月期限的年份
        today_month = today_month + 12 # 加12個月
    if today_month - RevisedMonth(revised_date) > 3 : # 超過三個月
        return False
    if today_month - RevisedMonth(revised_date) == 3 : # 等於三個月
        if today.day >= int(revised_date[len(revised_date)-2:]) : # 登入的日期大於三個月期限的日期
            return False
        else :
            return True
    return True

def CheckPassSame(host_id, new_pass) : # 檢查是否與前3次密碼相同
    all_pass = UserList.objects.filter(id = host_id)
    if make_password(new_pass, golden_key) == all_pass[0].passward or make_password(new_pass, golden_key) == all_pass[0].passward1 or make_password(new_pass, golden_key) == all_pass[0].passward2 :
        return False
    return True
    
def CheckLog(host_ip) : # 檢查在2分鐘內是否登入失敗兩次以上
    all_login_log = LoginLog.objects.all()
    fail_log_time = []
    for each_log in all_login_log :
        if host_ip == each_log.ip and each_log.successful == "0" : # 當 ip 相同且登入失敗
            fail_log_time.append(each_log.time[11:])
    now_min = str(datetime.datetime.today())[11:16] # 現在的小時跟分鐘
    count_fail_log = 0
    for each_fail_log in fail_log_time : # 每個失敗 log
        # 如果小時一樣，且現在分鐘-失敗log<=1(在一到兩分鐘以內)
        if each_fail_log[:2] == now_min[:2] and (abs(int(now_min[3:5])-int(each_fail_log[3:5])) <= 1) :
            # print(abs(int(now_min[3:5])-int(each_fail_log[3:5])))
            count_fail_log = count_fail_log + 1 # 在2分鐘內登入失敗有幾個
    if count_fail_log >= 2 : # 大於兩次失敗就先不能登入
        return True
    return False
    
def TodoBar(request) : # 近七日操作柱狀圖
    this_week, self_append, self_delete = CountTodoBar() # 這星期日期, 新增日期, 刪除日期
    c = (
        Bar()
            .add_xaxis(this_week)
            .add_yaxis("未完成", self_append)
            .add_yaxis("已完成", self_delete)
            .set_global_opts(title_opts=opts.TitleOpts(title="這七天的活動", subtitle="柱狀圖"))
    )
    return HttpResponse(c.render_embed())

def CountTodoBar() : # 計算七日內所有該使用者的新增、刪除事項
    all_todo = TodoList.objects.filter(user=host_id)
    this_week = [] # 這禮拜日期
    self_append = [0 for i in range(7)] # 哪幾天有新增事項
    self_delete = [0 for i in range(7)] # 哪幾天有刪除事項
    for i in range(7) :
        this_week.append(str(date.today()-timedelta(days=i)))
    this_week.reverse() # 從七天前
    for each_todo in all_todo : # 檢查每個事項
        if each_todo.time in this_week : # 在一個星期內的
            if each_todo.is_deleted == "0" : # 新增
                self_append[this_week.index(each_todo.time)] = self_append[this_week.index(each_todo.time)] + 1
            else : # 刪除
                self_delete[this_week.index(each_todo.time)] = self_delete[this_week.index(each_todo.time)] + 1
    return this_week, self_append, self_delete

def LoginPie(request) : # 登入裝況圓餅圖
    percent = CountLogin()
    pie = (
        Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="450px", height="250px"))
            # theme = 背景. width, height = 網頁大小
            .add("", list(zip(['成功', '失敗'], percent)), center = ["73%", "50%"])
            # center = 圓餅圖位置
            .set_colors(["red","black"]) # list
            .set_global_opts(title_opts=opts.TitleOpts(title="登入狀況", subtitle="圓餅圖", pos_left='5%'), legend_opts=opts.LegendOpts(pos_left="20%", pos_bottom="200px"))
            # legend_opts 小標籤
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}\n({d}%)"))
            # b = 字串, c = 數量, d = 百分比
    )
    return HttpResponse(pie.render_embed())

def CountLogin() : # 登入失敗比例
    login_success = LoginLog.objects.filter(successful="1")
    login_fail = LoginLog.objects.filter(successful="0")
    return [len(login_success), len(login_fail)]

def OutToExcel() : # 輸出 todo 為 excel 檔
    workbook = openpyxl.Workbook()
    # 取得第一個工作表
    all_not_done = TodoList.objects.filter(user = host_id, is_deleted = "0") # 還沒完成
    all_done = TodoList.objects.filter(user = host_id, is_deleted = "1") # 已完成
    not_done_list = ['未完成']
    done_list = ['已完成']
    sheet = workbook.worksheets[0]
    sheet['A1'] = '未完成'
    sheet['B1'] = '已完成'
    for i in range(len(all_not_done)) :
        not_done_list.append(all_not_done[i].things)
        sheet['A'+str(i+2)] = all_not_done[i].things
    for i in range(len(all_done)) :
        done_list.append(all_done[i].things)
        sheet['B'+str(i+2)] = all_done[i].things
    # 設定 sheet 工作表 A1 儲存格內容為 "Hello Python, Hello Excel."
    # 儲存檔案
    workbook.save('/var/www/html/Test/myproject/media/Excel/' + str(host_id) + '.xlsx')
    data = OrderedDict()
    data.update({"Sheet 1": [not_done_list, done_list]})
    save_data("/var/www/html/Test/myproject/media/Excel/" + str(host_id) + '.ods', data)

def OutToWord() : # 輸出使用者資訊為 word 檔
    document = Document() # docx
    odt = OpenDocumentText() # odt
    records = UserList.objects.all() # 全使用者資訊
    table = document.add_table(rows=1, cols=11) # 新增一個 table
    hdr_cells = table.rows[0].cells 
    hdr_cells[0].text = 'name' # docx 第一行元素
    hdr_cells[1].text = 'Id'
    hdr_cells[2].text = 'ip'
    odt.text.addElement(P(text = 'name  Id Ip')) # odt 第一行元素
    for i in records:
        row_cells = table.add_row().cells
        row_cells[0].text = i.name # docx 使用者資訊
        row_cells[1].text = str(i.id)
        row_cells[2].text = i.ip
        odt.text.addElement(P(text = i.name + " " + str(i.id) + " " + i.ip)) # odt 使用者資訊 
    document.save("/var/www/html/Test/myproject/media/Word/" + str(host_id) + '.docx')
    odt.save("/var/www/html/Test/myproject/media/Word/" + str(host_id), True)

def AddAccount(request) : # 新增帳號
    form = LoginForm1(request.POST, request.FILES)
    cursor = connection.cursor()
    cursor.execute("select * from ConnectSql_userlist")
    rows = cursor.fetchall()
    context = {'record' : rows, 'form' : form, 'ale' : False, 'cap' : Cap}
    if "send" in request.POST :
        if form.is_valid(): # 繳交新增的帳密
            # 輸入空值，回傳輸入無效
            #if not (form.cleaned_data['name']!=None and form.cleaned_data['passward']!=None and form.cleaned_data['image']!=None) :
            if not (form.cleaned_data['name']!=None and form.cleaned_data['passward']!=None) :
                context = {'cap' : Cap, 'record' : rows, 'form' : form, 'ale' : True}
                return render(request, "Test.html", context)
            #if (request.POST.get("g-recaptcha-response")=="") or (not Cap(request.POST).is_valid()): # login certification
            if not Cap(request.POST).is_valid(): # login certification
                context = {'cap' : Cap, "form" : form,  'ale_cap' : True, 'record' : rows}
                return render(request, "Test.html", context)
            for user in UserList.objects.all() : # 檢查帳號是否已註冊過
                if user.name == form.cleaned_data['name'] : # 有重複的帳號
                    context = {'cap' : Cap, 'record' : rows, 'form' : form, 'ale_1' : True}
                    return render(request, "Test.html", context)
            format_value = LetterFormat(form.cleaned_data['passward']) # 回傳密碼的型態
            if format_value == 0 : # 有大小寫，但長度不對
                context = {'record' : rows, 'form' : form, 'ale_2' : True, 'cap' : Cap}
                return render(request, "Test.html", context)
            if format_value == -1 : # 沒大小寫
                context = {'record' : rows, 'form' : form, 'ale_3' : True, 'cap' : Cap}
                return render(request, "Test.html", context)
            # 符合格式，新增帳號
            form.save()
            # 密碼加密
            sql_encrytion = "update ConnectSql_userlist set passward = %s where name = %s"
            cursor.execute(sql_encrytion, (make_password(form.cleaned_data['passward'], golden_key), form.cleaned_data['name']),)
            form = LoginForm1() # 每次繳交後清空 form
            back = True # 新增完帳密，導回登入頁面
            context = {"back" : back}
            return render(request, "Test.html", context)
    return render(request, "Test.html", context)

def Login(request) : # 登入頁面
    cursor = connection.cursor()
    form = LoginForm(request.POST or None)
    if "send" in request.POST :
        if form.is_valid() : # 提交帳號密碼
            ale = False # 登入成功要跳出
            cursor.execute("select name, id, passward from ConnectSql_userlist")
            record = cursor.fetchall()
            # 登入 log
            sql_update_loginlog = "insert into ConnectSql_loginlog(name, ip, successful, time) values(%s, %s, %s, %s)"
            if CheckLog(form.cleaned_data['ip']) : # 相同ip在1~2分鐘內超過兩次登入失敗
                context = {"log_fail" : True, "form" : form, 'cap' : Cap}
                return render(request, "Login.html", context)
            for name, id, passward in record : # 所有使用者的資料
                if form.cleaned_data['name'] == name and make_password(form.cleaned_data['passward'], golden_key) == passward :
                    # 登入成功
                    if not CheckRevised(datetime.date.today(), UserList.objects.filter(id=id)[0].revised_date) :
                        cursor.execute(sql_update_loginlog, (form.cleaned_data['name'], form.cleaned_data['ip'], "0", datetime.datetime.today())) # 登入失敗
                        form = LoginForm() # 清空
                        context = {"ale_revised" : True, "form" : form, 'cap' : Cap}
                        return render(request, "Login.html", context)
                    global host_id
                    host_id = id
                    global user_name
                    user_name = name
                    sql_update_ip = f"update ConnectSql_userlist set ip = %s where id = {host_id}"
                    sql_login= "update ConnectSql_userlist set status = 1 where id = %s" # 登入失敗回登入頁面
                    # 每次登入都要更新 ip 位址
                    cursor.execute(sql_update_ip, (form.cleaned_data['ip'],))
                    cursor.execute(sql_login, (host_id,))
                    cursor.execute(sql_update_loginlog, (form.cleaned_data['name'], form.cleaned_data['ip'], "1", datetime.datetime.today()))
                    context = {"ale" : True, "user_name" : user_name, 'cap' : Cap, "host_id" : host_id}
                    return render(request, "Login.html", context) # 登入成功
            cursor.execute(sql_update_loginlog, (form.cleaned_data['name'], form.cleaned_data['ip'], "0", datetime.datetime.today())) # 登入失敗
            form = LoginForm() # 清空
            context = {"form" : form, "ale" : ale, 'cap' : Cap}
            return render(request, "Login.html", context) # 登入失敗回登入頁面
    context = {"form" : form, 'cap' : Cap}
    return render(request, "Login.html", context)

def Normal(request) : # 一般使用者介面
    cursor = connection.cursor()
    try : # 確認 host_id 存在，防止 bug
        host_id
    except NameError : # 不存在就回登入頁面
        return Login(request)
    ale = False # 新增成功警告
    all_todo = TodoList.objects.filter(user=host_id, is_deleted = "0") # 所有該使用者的事項
    all_todo_del = TodoList.objects.filter(user=host_id, is_deleted = "1") # 所有該使用者被刪除的事項
    all_todo_id = [] # 事項的id
    form1 = TodoForm(request.POST or None)
    if "download" in request.POST : # 下載文件
        OutToExcel() # 輸出 todo 到 excel
        OutToWord() # 輸出帳號到 word
        all_todo = TodoList.objects.filter(user=host_id, is_deleted = "0") # 所有該使用者的事項
        all_todo_del = TodoList.objects.filter(user=host_id, is_deleted = "1") # 所有該使用者被刪除的事項
        img_loca = UserList.objects.filter(id=host_id)[0].image # 圖位置
        context = {"form1" : form1, "download" : True, "all_todo" : all_todo, "all_todo_del" : all_todo_del, "user_name" : user_name, "img_loca" : img_loca, "host_id" : host_id}
        return render(request, "Normal.html", context)
    if "logout" in request.POST : # 登出
        sql_logout = "update ConnectSql_userlist set status = 0 where id = %s"
        cursor.execute(sql_logout, (host_id))
        return render(request, "Normal.html", {"logout": True})
    if "insert" in request.POST : # 新增事項
        form1 = TodoForm1(request.POST or None) # 只有 things 的 form，只需輸入新增項目
        if form1.is_valid() : # 有效的輸入
            sql_insert = "insert into ConnectSql_todolist(user, things, is_deleted, time) values(%s, %s, '0', %s)"
            cursor.execute(sql_insert, (host_id, form1.cleaned_data['things'],datetime.date.today(),))
            ale = True
            # 要再更新一次，因為是送出後才執行insert
            all_todo = TodoList.objects.filter(user=host_id, is_deleted = "0") # 所有該使用者的事項
            all_todo_del = TodoList.objects.filter(user=host_id, is_deleted = "1") # 所有該使用者被刪除的事項
            form1 = TodoForm() # 清空欄位
            img_loca = UserList.objects.filter(id=host_id)[0].image
            context = {"form1" : form1, "ale" : ale, "all_todo" : all_todo, "all_todo_del" : all_todo_del, "user_name" : user_name, "img_loca" : img_loca, "host_id" : host_id}
            return render(request, "Normal.html", context)
    if "edit" in request.POST : # 編輯事項
        if form1.is_valid() :
            for i in range(len(all_todo)) :
                all_todo_id.append(getattr(all_todo[i], 'id')) # 所有事項的id
            things = form1.cleaned_data['things']
            id = form1.cleaned_data['user']
            sql_update = f"UPDATE ConnectSql_todolist set things = %s WHERE user = {host_id} and id = %s"
            cursor.execute(sql_update, (things,all_todo_id[int(id)-1],)) # 輸入數字-1才會對到index
            ale = True
            # 要再更新一次，因為是送出後才執行insert
            all_todo = TodoList.objects.filter(user=host_id, is_deleted = "0") # 所有該使用者的事項
            all_todo_del = TodoList.objects.filter(user=host_id, is_deleted = "1") # 所有該使用者被刪除的事項
            form1 = TodoForm() # 清空欄位
            img_loca = UserList.objects.filter(id=host_id)[0].image
            context = {"form1" : form1, "ale" : ale, "all_todo" : all_todo, "all_todo_del" : all_todo_del, "user_name" : user_name, "img_loca" : img_loca, "host_id" : host_id}
            return render(request, "Normal.html", context)
    if "is_deleted" in request.POST : # 刪除事項
        form2 = TodoForm2(request.POST or None)
        if form2.is_valid() :
            for i in range(len(all_todo)) :
                all_todo_id.append(getattr(all_todo[i], 'id')) # 所有事項的id
            sql_delete = f"UPDATE ConnectSql_todolist set is_deleted = '1' WHERE user = {host_id} and id = %s"
            cursor.execute(sql_delete, (all_todo_id[int(form2.cleaned_data['user'])-1],))
            ale_delete = True # 警告已刪除
            all_todo = TodoList.objects.filter(user=host_id, is_deleted = "0") # 所有該使用者的事項
            all_todo_del = TodoList.objects.filter(user=host_id, is_deleted = "1") # 所有該使用者被刪除的事項
            form1 = TodoForm() # 清空欄位
            img_loca = UserList.objects.filter(id=host_id)[0].image
            context = {"form1" : form1, "ale_delete" : ale_delete, "all_todo" : all_todo, "all_todo_del" : all_todo_del, "user_name" : user_name, "img_loca" : img_loca, "host_id" : host_id}
            return render(request, "Normal.html", context)
    img_loca = UserList.objects.filter(id=host_id)[0].image
    context = {"form1" : form1, "ale" : ale, "all_todo" : all_todo, "all_todo_del" : all_todo_del, "user_name" : user_name, "img_loca" : img_loca, "host_id" : host_id}
    return render(request, "Normal.html", context)
    
def ChPassward(request) : # 更改密碼
    cursor = connection.cursor()
    form = ChForm(request.POST)
    if "send" in request.POST :
        if form.is_valid():
            cursor.execute("select name, id, passward from ConnectSql_userlist")
            record = cursor.fetchall()
            for name, id, passward in record : # 所有使用者的資料
                if form.cleaned_data['name'] == name and make_password(form.cleaned_data['passward'], golden_key) == passward :
                    # 登入成功
                    global host_id
                    host_id = id
                    global user_name
                    user_name = name
                    if not CheckPassSame(host_id, form.cleaned_data['passward1']) : # 密碼與前三次相同
                        context = {"form" : form, "ale_pass_used" : True}
                        return render(request, "ChPassward.html", context)
                    context = {"ale" : True, "user_name" : user_name}
                    # 把密碼都往後推
                    sql_up_pass = "update ConnectSql_userlist set passward = %s where id = %s" # 把 passward 改成最新密碼
                    sql_up_pass1 = "update ConnectSql_userlist set passward1 = passward where id = %s"
                    sql_up_pass2 = "update ConnectSql_userlist set passward2 = passward1 where id = %s"
                    # 更改 revised_date 為今天
                    sql_up_revised_date = "update ConnectSql_userlist set revised_date = %s where id = %s"
                    cursor.execute(sql_up_pass2, (host_id,))
                    cursor.execute(sql_up_pass1, (host_id,))
                    cursor.execute(sql_up_pass, (make_password(form.cleaned_data['passward1'], golden_key), host_id,))
                    cursor.execute(sql_up_revised_date, (datetime.date.today(), host_id,))
                    context = {"form" : form, "ale_success" : True} # 登入成功
                    return render(request, "ChPassward.html", context) 
            context = {"form" : form, "ale_wrong" : True} # 密碼錯誤
            return render(request, "ChPassward.html", context)
    context = {"form" : form}
    return render(request, "ChPassward.html", context)

def Port(request) :
    return HttpResponse("188")

def Hw(request) :
    cursor = connection.cursor()
    cursor.execute("select * from ConnectSql_hwdata;")
    record = cursor.fetchall()
    form = HwForm(request.POST or None)
    num = randint(0,len(record)-1)
    context = {"leng" : len(str(record[num][1])), "ans" : record[num][1], "form" :form}
    if "insert_text" in request.POST : 
        if form.is_valid(): # 繳交新增的帳密
            sql = "insert into ConnectSql_hwdata(eng_ans) values(%s);"
            cursor.execute(sql, (form.cleaned_data["eng_ans"],))
            return render(request, "Hw.html", context)
    return render(request, "Hw.html", context)
