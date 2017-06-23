# 系统配置管理

系统配置主要是对一些系统相关的数据配置，包括数据库，日志配置。

> 注意，系统配置影响系统的运行状态，所有操作必须由超级管理员完成。

## 基本配置

- DEBUG 选项，设置系统的调试开关，用于诊断系统故障
- 时区：目前仅支持中国时区

## 数据库配置

数据库连接池性能调整，一般无需改动。

- 数据库DEBUG：开启此项，会在控制台打印sql，数据量很大，一般情况下禁用。
- 连接池大小：如果使用MySQL等支持连接池的数据库，可以根据数据库的性能调节此参数。
- 连接池回收间隔（秒）：每隔一段时间，回收未使用的数据库连接

#### MySQL数据库初始化参考

进入 mysql 终端管理, 执行以下语句：

    > mysql >  create database taurusxr DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;

    > mysql >  GRANT ALL ON taurusxr.* TO raduser@'127.0.0.1' IDENTIFIED BY 'radpwd' WITH GRANT OPTION;

    > mysql >  FLUSH PRIVILEGES; 

修改数据库配置部分,具体参数请根据实际填写。

    "database": {
        "backup_path": "/var/taurusxr/data",
        "dbtype": "mysql",
        "dburl": "mysql://raduser:radpwd@127.0.0.1:3306/taurusxr?charset=utf8",
        "echo": 0,
        "pool_recycle": 300,
        "pool_size": 60
    }


## 日志配置

可支持外部 syslog 服务。

- 开启syslog：是否启用syslog
- syslog 服务器：syslog服务器的 IP 地址
- syslog 服务端口(UDP)：syslog端口
- 日志级别：日志打印级别

## 高可用设置

提供系统双机互备能力，需要两台服务器，提供应用级别的数据复制，自动解决数据冲突。

- 启用双机热备：是否启用
- 同步数据检测间隔：每隔一段时间检测数据变化，最低支持1秒
- 同步链路检测间隔：心跳检测间隔
- 主机地址：主服务器地址，格式为 tcp://IP地址(或域名):端口
- 备机地址：备服务器地址，格式为 tcp://IP地址(或域名):端口

> 注意，修改高可用配置后，必须在[系统服务器状态管理](/admin/superrpc)页面重启同步服务。




