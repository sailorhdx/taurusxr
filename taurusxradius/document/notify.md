# 通知模版管理

通知模版是用来生成一些系统的通知内容的，并不是所有的通知都需要模版，主要某些应用场景为了实现标准化的格式，以及大部分短信服务商也要求使用模版。

目前系统内置了以下几种通知模版，可以根据需要进行修改：

- 用户开户通知模板 - open_notify
- 用户续费通知模板 - next_notify
- 用户到期通知模板 - expire_notify
- 装机工单通知模板 - install_notify
- 维修工单通知模板 - maintain_notify

## 模版格式注意事项

如以下模版：

    > 尊敬的{customer_name}您好,欢迎使用我公司的{product_name},您的账号是{username}，密码是{password}，套餐使用至{expire_date}

其中{xxx}部分是用来做替换的变量，可以根据需要改变位置，但不要修改其中的名称。

