#校园失物招领平台
#项目介绍
针对大学校园内师生频繁丢失或拾获物品，但信息流通不畅、寻回效率低下的问题，设计并开发一个集信息发布、智能检索、实时匹配、地图定位与通知功能于一体的校园失物招领网络平台。该系统旨在简化失物招领流程，提高物品归还的成功率。
#功能
前端界面:
  用户注册与登录功能。
  信息发布功能：用户可以发布“失物信息”或“拾物信息”，需包含物品名称、描述、丢失/拾获时间、地点，并支持上传物品图片。
  信息展示墙：以时间线或卡片流的形式展示最新的失物与拾物信息。
  搜索功能：支持通过关键词、物品分类、丢失/拾获日期等条件进行模糊搜索。
  个人中心：用户可以管理自己发布的帖子（编辑、删除、标记为“已找回”）。
后端服务:
  用户认证与管理：提供安全的用户身份验证和个人信息管理。
  数据存储：设计合理的数据库结构，存储用户信息、物品信息及图片。
  API接口：提供RESTful API，支持前端进行数据的增、删、改、查操作。
高级功能 ：
  智能匹配与推送: 当有新的“失物”信息发布时，系统自动在“拾物”数据库中进行匹配（基于关键词、分类等），并将高度相似的条目推送给失主。反之亦然。
  地图集成: 集成校园地图API，允许用户在地图上精确标记物品丢失或拾获的位置，并支持按地理位置进行筛选。
  站内信/即时通讯: 用户可以对感兴趣的帖子发送私信进行沟通，无需公开个人联系方式，保护用户隐私。
  邮件/短信提醒: 当有疑似物品匹配或收到新的私信时，通过邮件或短信向用户发送提醒。
#使用说明
目前支持在bupt局域网内使用
打开网站首页 http://10.122.197.122:8000/
