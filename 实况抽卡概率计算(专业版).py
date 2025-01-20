import tkinter as tk
import webbrowser
from tkinter import simpledialog

# 全局变量
a0, a, b, c, d, e, e2 = 0, 0, 0, 0, 0, 0, 0

def setup():
    print("Setting up...")

# 初始化窗口
root = tk.Tk()
root.geometry('450x280')
root.title("实况抽卡概率计算")

# 调用初始化函数
setup()

# 作者信息
def open_link(url):
    webbrowser.open(url)

def author():
    author_win = tk.Toplevel()
    author_win.title("作者")
    author_win.geometry('300x270')

    # 邮箱
    email_label = tk.Label(author_win, text="Outlook：sss15006")
    email_label.place(x=110, y=30, anchor="center")
    def copy_email():
        author_win.clipboard_clear()
        author_win.clipboard_append("sss15006@outlook.com")
        author_win.update()

    copy_email_button = tk.Button(author_win, text="复制", command=copy_email)
    copy_email_button.place(x=250, y=30, anchor="center")

    # QQ
    qq_label = tk.Label(author_win, text="QQ：3192491461", fg="black", cursor="hand2")
    qq_label.place(x=110, y=70, anchor="center")
    def copy_qq():
        author_win.clipboard_clear()
        author_win.clipboard_append("3192491461")
        author_win.update()
    copy_qq_button = tk.Button(author_win, text="复制", command=copy_qq)
    copy_qq_button.place(x=250, y=70, anchor="center")
    
    # 评球
    pq_label = tk.Label(author_win, text="大众评球：mc方", fg="black", cursor="hand2")
    pq_label.place(x=110, y=110, anchor="center")
    def copy_pq():
        author_win.clipboard_clear()
        author_win.clipboard_append("mc方")
        author_win.update()
    copy_pq_button = tk.Button(author_win, text="复制", command=copy_pq)
    copy_pq_button.place(x=250, y=110, anchor="center")

    # 实况
    efootball_label = tk.Label(author_win, text="实况id：983736108", fg="black", cursor="hand2")
    efootball_label.place(x=110, y=150, anchor="center")
    def copy_efootball():
        author_win.clipboard_clear()
        author_win.clipboard_append("983736108")
        author_win.update()
    copy_efootball_button = tk.Button(author_win, text="复制", command=copy_efootball)
    copy_efootball_button.place(x=250, y=150, anchor="center")
    
    # GitHub 链接
    github_label = tk.Label(author_win, text="Github：ssyPromax", fg="blue", cursor="hand2")
    github_label.place(x=110, y=190, anchor="center")
    def copy_github():
        author_win.clipboard_clear()
        author_win.clipboard_append("https://github.com/ssyPromax")
        author_win.update()
    github_label.bind("<Button-1>", lambda event: open_link("https://github.com/ssyPromax"))
    copy_github_button = tk.Button(author_win, text="复制", command=copy_github)
    copy_github_button.place(x=250, y=190, anchor="center")
    
    # B站链接
    bilibili_label = tk.Label(author_win, text="B站: 没能力的赵鹏", fg="blue", cursor="hand2")
    bilibili_label.place(x=110, y=230, anchor="center")
    def copy_bilibili():
        author_win.clipboard_clear()
        author_win.clipboard_append("https://space.bilibili.com/677960956")
        author_win.update()
    bilibili_label.bind("<Button-1>", lambda event: open_link("https://space.bilibili.com/677960956"))
    copy_bilibili_button = tk.Button(author_win, text="复制", command=copy_bilibili)
    copy_bilibili_button.place(x=250, y=230, anchor="center")
    
# 定义输入函数
def get_a0():
    global a0
    input_a0 = simpledialog.askstring("5星球员概率", "请输入5星球员概率(%):")
    if input_a0 is None:  # 用户取消输入
        return
    try:
        a0 = 0.01 * int(input_a0)
        a0_label.config(text=f"{input_a0}%")
    except ValueError:
        a0_label.config(text="NaN")

def get_a():
    global a
    input_a = simpledialog.askstring("5星球员数量", "请输入5星球员数量:")
    if input_a is None:
        return
    try:
        a = int(input_a)
        a_label.config(text=input_a)
    except ValueError:
        a_label.config(text="NaN")

def get_b():
    global b
    input_b = simpledialog.askstring("高光/黄传/精选球员数量", "请输入高光/黄传/精选球员数量:")
    if input_b is None:
        return
    try:
        b = int(input_b)
        b_label.config(text=input_b)
    except ValueError:
        b_label.config(text="NaN")

def get_c():
    global c
    input_c = simpledialog.askstring("金币十连抽次数", "请输入金币十连抽次数:")
    if input_c is None:
        return
    try:
        c = int(input_c)
        c_label.config(text=input_c)
    except ValueError:
        c_label.config(text="NaN")

def get_d():
    global d
    input_d = simpledialog.askstring("券单抽次数", "请输入券抽取次数:")
    if input_d is None:
        return
    try:
        d = int(input_d)
        d_label.config(text=input_d)
    except ValueError:
        d_label.config(text="NaN")

# 定义计算函数
def calc():
    global e, e2  # 确保 e 和 e2 是全局变量
    selected_option = var.get()

    if selected_option == 1:
        if a0 != 0 and a != 0 and b != 0:
            e = a0 * (b / a)
            e2 = 1 - e
        else:
            e, e2 = 0, 1  # 默认值，避免未初始化的错误

        c_local = 10 * c  # 使用局部变量处理计算逻辑
        p0 = round(100 * (e2 ** c_local) * (0.9 ** d), 2)
        p0_label.config(text=f"不出的概率: {p0}%")

        p1 = round(100 * ((e2 ** (c_local - 1) * (c_local * e)) * (0.9 ** d) + (e2 ** c_local) * (0.9 ** (d - 1) * 0.1 * d)), 2)
        p1_label.config(text=f"出一个的概率: {p1}%")

        p2 = round(100 * ((e2 ** (c_local - 2) * (c_local * (c_local - 1) / 2) * (e) ** 2) * (0.9 ** d) +
                          (e2 ** c_local) * (0.9 ** (d - 2) * (d * (d - 1) / 2) * 0.01) +
                          (e2 ** (c_local - 1) * (c_local * e)) * (0.9 ** (d - 1) * 0.1 * d)), 2)
        p2_label.config(text=f"出两个的概率: {p2}%")

        p3 = abs(round(100 - p0 - p1 - p2, 2))
        p3_label.config(text=f"出两个以上的概率: {p3}%")
        p3_label.place(x=380, y=160, anchor="e")  # 显示 p3_label

    elif selected_option == 2:
        if a0 != 0 and a != 0 and b != 0:
            e = a0 * (b / a)
            e2 = 1 - e
        else:
            e, e2 = 0, 1  # 默认值，避免未初始化的错误

        c_local = c  # 使用局部变量处理计算逻辑
        p0 = round(100 * ((e2 ** 9) * (1 - (b / a))) ** c_local * 0.9 ** d, 2)
        p0_label.config(text=f"不出的概率: {p0}%")

        p1 = round(100 * (e2 ** (9 * c_local - 1) * e * 9 * c_local) * (1 - (b / a)) ** c_local * 0.9 ** d +
                   (e2 ** 9) * (1 - (b / a)) ** (c_local - 1) * (b / a) * c_local * 0.9 ** d +
                   (e2 ** 9) * (1 - (b / a)) ** c_local * 0.9 ** (d - 1) * 0.1 * d, 2)
        p1_label.config(text=f"出一个的概率: {p1}%")

        p2 = abs(round(100 - p0 - p1, 2))
        p2_label.config(text=f"出一个以上的概率: {p2}%")

        # 删除 p3_label
        p3_label.place_forget()

# 创建标签和按钮
author_button = tk.Button(root, text="作者", command=author)
author_button.place(x=400, y=250, anchor="e")
author_button.config(width=10, height=1)

a0_label = tk.Label(root, text="0")
a0_label.place(x=200, y=30, anchor="e")
get_a0_button = tk.Button(root, text="5星球员概率", command=get_a0)
get_a0_button.place(x=150, y=30, anchor="e")

a_label = tk.Label(root, text="0")
a_label.place(x=200, y=70, anchor="e")
get_a_button = tk.Button(root, text="5星球员数量", command=get_a)
get_a_button.place(x=150, y=70, anchor="e")

b_label = tk.Label(root, text="0")
b_label.place(x=200, y=110, anchor="e")
get_b_button = tk.Button(root, text="高光/黄传/精选球员数量", command=get_b)
get_b_button.place(x=150, y=110, anchor="e")

c_label = tk.Label(root, text="0")
c_label.place(x=200, y=150, anchor="e")
get_c_button = tk.Button(root, text="金币十连抽次数", command=get_c)
get_c_button.place(x=150, y=150, anchor="e")

d_label = tk.Label(root, text="0")
d_label.place(x=200, y=190, anchor="e")
get_d_button = tk.Button(root, text="券单抽次数", command=get_d)
get_d_button.place(x=150, y=190, anchor="e")

p0_label = tk.Label(root, text="")
p0_label.place(x=380, y=100, anchor="e")
p1_label = tk.Label(root, text="")
p1_label.place(x=380, y=120, anchor="e")
p2_label = tk.Label(root, text="")
p2_label.place(x=380, y=140, anchor="e")
p3_label = tk.Label(root, text="")
p3_label.place(x=380, y=160, anchor="e")  # 默认显示 p3_label

get_calc_button = tk.Button(root, text="计算", command=calc)
get_calc_button.config(width=15, height=1)
get_calc_button.place(x=270, y=50)

# 单选按钮
var = tk.IntVar()
var.set(1)
Normal = tk.Radiobutton(root, text="普通包", variable=var, value=1)
Normal.place(x=250, y=20)
Guarantees = tk.Radiobutton(root, text="保黑包", variable=var, value=2)
Guarantees.place(x=330, y=20)

# 启动主循环
root.mainloop()
