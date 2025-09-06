import asyncio
from email.message import EmailMessage

import aiosmtplib

import json

data = {
    "input_message": """最新的财新周刊封面报道：

1. 标题：封面报道之二｜越南革新新局
 链接：https://weekly.caixin.com/2025-08-30/102357052.html
 摘要：对内机构改革做大手术，对外“竹子外交”求平衡
 时间：2025-08-30 09:27:53

2. 标题：封面报道｜“到越南去”历经多轮热潮 当下进还是退？
 链接：https://weekly.caixin.com/2025-08-29/102356689.html
 摘要：“链主”企业带动上游供应商纷至沓来，新兴的“世界组装厂”越南为中国企业带来什么机会？
 时间：2025-08-29 15:58:39

3. 标题：封面报道之二｜商品期货市场宽幅波动 “反内卷”行情将如何演绎？
 链接：https://weekly.caixin.com/2025-08-23/102354609.html
 摘要：多晶硅、焦煤、碳酸锂三大主力期货近月暴涨暴跌，市场情绪一度亢奋，押注新一轮去产能
 时间：2025-08-29 09:25:23

4. 标题：封面报道｜寻找“慢牛”
 链接：https://weekly.caixin.com/2025-08-22/102354340.html
 摘要：资金蜂拥而至之时，市场呼唤一系列着眼中长期的制度建设
 时间：2025-08-22 16:03:32

5. 标题：封面报道之二｜灵活用工的社保挑战
 链接：https://weekly.caixin.com/2025-08-16/102352604.html
 摘要：新经济就业形态灵活、职业多元化，社保缴纳强化执法影响几何？
 时间：2025-08-16 10:23:27"""
}

# 处理为邮件正文
lines = data["input_message"].split("\n\n")
email_body = ""
for item in lines:
    email_body += item + "\n" + "-"*50 + "\n"

print(email_body)

# ========== 配置区 ==========
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 587
FROM_EMAIL = "690058381@qq.com"         # ⚠️ 修改为你的 QQ 邮箱
EMAIL_AUTH_CODE = "ddcsqzqqkogsbeib"         # ⚠️ 修改为你在 QQ 邮箱设置中获取的授权码

TO_EMAIL = FROM_EMAIL  # 如果是发给自己，也可以改成其他人
SUBJECT = "测试邮件：来自 NAT"
CONTENT = email_body
# ===========================


async def send_test_email():
    message = EmailMessage()
    message["From"] = FROM_EMAIL
    message["To"] = TO_EMAIL
    message["Subject"] = SUBJECT
    message.set_content(CONTENT)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=FROM_EMAIL,
            password=EMAIL_AUTH_CODE,
            start_tls=True,
        )
        print("✅ 邮件发送成功！请查收你的邮箱。")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


if __name__ == "__main__":
    asyncio.run(send_test_email())
