# 企业内部 IT 报修与资产运维管理平台后端 API 接口文档

## 1. 项目说明

本项目为企业内部 IT 报修与资产运维管理平台，主要提供以下业务能力：

1. 员工登录系统并提交 IT 报修工单；
2. IT 运维人员查看、接单、处理、完成工单；
3. 管理员维护用户、资产分类、资产台账；
4. 系统记录工单状态流转、维修记录、操作日志；
5. 提供统计接口，用于首页看板展示。

后端要求使用：

```text
Python 3.11+
FastAPI
SQLAlchemy
Pydantic
MySQL 8.0
JWT Token 认证
```

接口统一前缀：

```text
/api/v1
```

本接口文档对应的主要数据库表：

```text
sys_user              用户表
it_asset_category     资产分类表
it_asset              资产表
it_ticket             报修工单表
it_ticket_record      工单流转记录表
it_repair_record      维修记录表
it_faq                常见问题表
sys_operation_log     操作日志表
```

---

# 2. 通用规范

## 2.1 统一响应格式

所有接口返回统一 JSON 格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

字段说明：

| 字段      | 类型                    | 说明                    |
| ------- | --------------------- | --------------------- |
| code    | int                   | 业务状态码，0 表示成功，非 0 表示失败 |
| message | string                | 响应提示信息                |
| data    | object / array / null | 具体业务数据                |

失败示例：

```json
{
  "code": 40001,
  "message": "用户名或密码错误",
  "data": null
}
```

---

## 2.2 HTTP 状态码规范

| HTTP 状态码 | 说明                   |
| -------- | -------------------- |
| 200      | 请求成功                 |
| 201      | 创建成功                 |
| 400      | 请求参数错误               |
| 401      | 未登录或 Token 无效        |
| 403      | 无权限访问                |
| 404      | 资源不存在                |
| 409      | 业务冲突，例如用户名重复、状态不允许流转 |
| 422      | 参数校验失败               |
| 500      | 服务器内部错误              |

---

## 2.3 业务错误码

| code  | 说明            |
| ----- | ------------- |
| 0     | 成功            |
| 40000 | 参数错误          |
| 40001 | 用户名或密码错误      |
| 40002 | 用户已被禁用        |
| 40100 | 未登录或 Token 无效 |
| 40300 | 无权限操作         |
| 40400 | 资源不存在         |
| 40900 | 业务状态冲突        |
| 50000 | 系统内部错误        |

---

## 2.4 分页请求参数

列表接口统一支持分页参数：

| 参数        | 类型  | 必填 | 默认值 | 说明          |
| --------- | --- | -- | --- | ----------- |
| page      | int | 否  | 1   | 当前页码        |
| page_size | int | 否  | 10  | 每页数量，最大 100 |

分页响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 10,
    "pages": 10
  }
}
```

---

## 2.5 认证方式

除登录接口外，其他接口默认都需要携带 JWT Token。

请求头格式：

```http
Authorization: Bearer <access_token>
```

---

# 3. 枚举值定义

## 3.1 用户角色 role

| 值        | 说明      |
| -------- | ------- |
| admin    | 管理员     |
| it_staff | IT 运维人员 |
| employee | 普通员工    |

---

## 3.2 用户状态 status

| 值 | 说明 |
| - | -- |
| 1 | 启用 |
| 0 | 禁用 |

---

## 3.3 工单状态 ticket.status

| 值          | 说明  |
| ---------- | --- |
| pending    | 待受理 |
| assigned   | 已派单 |
| processing | 处理中 |
| completed  | 已完成 |
| cancelled  | 已取消 |

第一版先使用以上 5 个状态，不要增加过多状态。

---

## 3.4 工单优先级 priority

| 值      | 说明 |
| ------ | -- |
| low    | 低  |
| normal | 普通 |
| high   | 高  |
| urgent | 紧急 |

---

## 3.5 故障类型 fault_type

| 值        | 说明     |
| -------- | ------ |
| hardware | 硬件故障   |
| software | 软件故障   |
| network  | 网络故障   |
| printer  | 打印机故障  |
| account  | 账号权限问题 |
| other    | 其他     |

---

## 3.6 资产状态 asset.status

| 值         | 说明  |
| --------- | --- |
| in_use    | 在用  |
| idle      | 闲置  |
| repairing | 维修中 |
| scrapped  | 已报废 |

---

## 3.7 维修结果 repair_result

| 值              | 说明      |
| -------------- | ------- |
| fixed          | 已修复     |
| replace_repair | 更换配件后修复 |
| scrapped       | 建议报废    |
| unresolved     | 未解决     |

---

# 4. 权限规则

## 4.1 普通员工 employee

允许：

```text
查看自己的信息
修改自己的密码
创建自己的报修工单
查看自己的工单列表
查看自己的工单详情
取消自己的 pending 状态工单
```

不允许：

```text
查看全部用户
管理资产
派单
处理工单
查看操作日志
```

---

## 4.2 IT 运维人员 it_staff

允许：

```text
查看工单列表
查看工单详情
接单
开始处理工单
完成工单
查看资产列表
查看资产详情
查看维修记录
```

不允许：

```text
删除用户
禁用用户
删除资产
查看系统操作日志
```

---

## 4.3 管理员 admin

允许：

```text
用户管理
资产分类管理
资产管理
工单管理
派单
查看所有工单
查看维修记录
查看操作日志
查看统计数据
```

---

# 5. 认证模块 Auth API

## 5.1 用户登录

```http
POST /api/v1/auth/login
```

权限：公开接口

请求参数：

```json
{
  "username": "admin",
  "password": "123456"
}
```

字段说明：

| 字段       | 类型     | 必填 | 说明    |
| -------- | ------ | -- | ----- |
| username | string | 是  | 登录用户名 |
| password | string | 是  | 登录密码  |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "jwt_token_string",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "admin",
      "real_name": "系统管理员",
      "role": "admin",
      "department": "信息部",
      "phone": "13800000001",
      "email": "admin@example.com",
      "status": 1
    }
  }
}
```

业务规则：

```text
1. 根据 username 查询用户；
2. 用户不存在，返回用户名或密码错误；
3. 密码校验失败，返回用户名或密码错误；
4. 用户 status = 0，返回账号已禁用；
5. 登录成功后生成 JWT Token；
6. 记录登录操作日志。
```

---

## 5.2 获取当前登录用户

```http
GET /api/v1/auth/me
```

权限：登录用户

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "admin",
    "real_name": "系统管理员",
    "role": "admin",
    "department": "信息部",
    "phone": "13800000001",
    "email": "admin@example.com",
    "status": 1,
    "created_at": "2026-06-21 08:00:00"
  }
}
```

---

## 5.3 修改当前用户密码

```http
PUT /api/v1/auth/password
```

权限：登录用户

请求参数：

```json
{
  "old_password": "123456",
  "new_password": "NewPassword123"
}
```

字段说明：

| 字段           | 类型     | 必填 | 说明           |
| ------------ | ------ | -- | ------------ |
| old_password | string | 是  | 原密码          |
| new_password | string | 是  | 新密码，长度至少 6 位 |

成功响应：

```json
{
  "code": 0,
  "message": "密码修改成功",
  "data": null
}
```

业务规则：

```text
1. 校验 old_password 是否正确；
2. new_password 需要加密后保存；
3. 修改成功后记录操作日志。
```

---

# 6. 用户管理 User API

## 6.1 查询用户列表

```http
GET /api/v1/users
```

权限：admin

查询参数：

| 参数         | 类型     | 必填 | 说明                               |
| ---------- | ------ | -- | -------------------------------- |
| keyword    | string | 否  | 按用户名、姓名、手机号模糊查询                  |
| role       | string | 否  | 用户角色：admin / it_staff / employee |
| status     | int    | 否  | 用户状态：1启用，0禁用                     |
| department | string | 否  | 部门                               |
| page       | int    | 否  | 页码                               |
| page_size  | int    | 否  | 每页数量                             |

请求示例：

```http
GET /api/v1/users?keyword=张&role=it_staff&page=1&page_size=10
```

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 2,
        "username": "it_zhang",
        "real_name": "张工",
        "role": "it_staff",
        "department": "信息部",
        "phone": "13800000002",
        "email": "zhang@example.com",
        "status": 1,
        "created_at": "2026-06-21 08:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "pages": 1
  }
}
```

---

## 6.2 创建用户

```http
POST /api/v1/users
```

权限：admin

请求参数：

```json
{
  "username": "employee_chen",
  "password": "123456",
  "real_name": "陈强",
  "role": "employee",
  "department": "招商部",
  "phone": "13800000005",
  "email": "chenqiang@example.com",
  "status": 1
}
```

成功响应：

```json
{
  "code": 0,
  "message": "用户创建成功",
  "data": {
    "id": 5,
    "username": "employee_chen",
    "real_name": "陈强",
    "role": "employee",
    "department": "招商部",
    "phone": "13800000005",
    "email": "chenqiang@example.com",
    "status": 1
  }
}
```

业务规则：

```text
1. username 不允许重复；
2. password 必须加密后保存到 password_hash；
3. role 只能是 admin、it_staff、employee；
4. 创建成功后记录操作日志。
```

---

## 6.3 查询用户详情

```http
GET /api/v1/users/{user_id}
```

权限：admin

路径参数：

| 参数      | 类型  | 必填 | 说明   |
| ------- | --- | -- | ---- |
| user_id | int | 是  | 用户ID |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 3,
    "username": "employee_li",
    "real_name": "李明",
    "role": "employee",
    "department": "财务部",
    "phone": "13800000003",
    "email": "liming@example.com",
    "status": 1,
    "created_at": "2026-06-21 08:00:00",
    "updated_at": "2026-06-21 08:00:00"
  }
}
```

---

## 6.4 修改用户

```http
PUT /api/v1/users/{user_id}
```

权限：admin

请求参数：

```json
{
  "real_name": "李明",
  "role": "employee",
  "department": "财务部",
  "phone": "13800000003",
  "email": "liming@example.com",
  "status": 1
}
```

业务规则：

```text
1. 不允许通过该接口修改密码；
2. 不允许修改 username；
3. 修改用户信息后记录操作日志。
```

成功响应：

```json
{
  "code": 0,
  "message": "用户修改成功",
  "data": null
}
```

---

## 6.5 启用或禁用用户

```http
PATCH /api/v1/users/{user_id}/status
```

权限：admin

请求参数：

```json
{
  "status": 0
}
```

成功响应：

```json
{
  "code": 0,
  "message": "用户状态修改成功",
  "data": null
}
```

业务规则：

```text
1. status 只能为 1 或 0；
2. 不允许禁用当前登录的管理员自己；
3. 修改后记录操作日志。
```

---

## 6.6 重置用户密码

```http
PATCH /api/v1/users/{user_id}/password
```

权限：admin

请求参数：

```json
{
  "new_password": "123456"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "密码重置成功",
  "data": null
}
```

---

## 6.7 删除用户

```http
DELETE /api/v1/users/{user_id}
```

权限：admin

成功响应：

```json
{
  "code": 0,
  "message": "用户删除成功",
  "data": null
}
```

业务规则：

```text
1. 如果用户已经关联工单、资产、维修记录，不允许物理删除；
2. 已有关联数据时，返回 409，并建议使用禁用用户；
3. 不允许删除当前登录用户自己。
```

---

# 7. 资产分类 Asset Category API

## 7.1 查询资产分类列表

```http
GET /api/v1/asset-categories
```

权限：admin、it_staff

查询参数：

| 参数      | 类型     | 必填 | 说明      |
| ------- | ------ | -- | ------- |
| keyword | string | 否  | 分类名称或编码 |
| status  | int    | 否  | 1启用，0停用 |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "category_name": "办公电脑",
      "category_code": "PC",
      "description": "员工日常办公使用的台式机、笔记本电脑",
      "status": 1
    }
  ]
}
```

---

## 7.2 创建资产分类

```http
POST /api/v1/asset-categories
```

权限：admin

请求参数：

```json
{
  "category_name": "服务器设备",
  "category_code": "SERVER",
  "description": "服务器、存储等机房设备",
  "status": 1
}
```

成功响应：

```json
{
  "code": 0,
  "message": "资产分类创建成功",
  "data": {
    "id": 4
  }
}
```

业务规则：

```text
1. category_code 不允许重复；
2. category_name 不允许为空；
3. 创建成功后记录操作日志。
```

---

## 7.3 查询资产分类详情

```http
GET /api/v1/asset-categories/{category_id}
```

权限：admin、it_staff

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "category_name": "办公电脑",
    "category_code": "PC",
    "description": "员工日常办公使用的台式机、笔记本电脑",
    "status": 1,
    "created_at": "2026-06-21 08:00:00",
    "updated_at": "2026-06-21 08:00:00"
  }
}
```

---

## 7.4 修改资产分类

```http
PUT /api/v1/asset-categories/{category_id}
```

权限：admin

请求参数：

```json
{
  "category_name": "办公终端",
  "category_code": "PC",
  "description": "台式机、笔记本、一体机等办公终端设备",
  "status": 1
}
```

成功响应：

```json
{
  "code": 0,
  "message": "资产分类修改成功",
  "data": null
}
```

---

## 7.5 删除资产分类

```http
DELETE /api/v1/asset-categories/{category_id}
```

权限：admin

成功响应：

```json
{
  "code": 0,
  "message": "资产分类删除成功",
  "data": null
}
```

业务规则：

```text
1. 如果分类下已有资产，不允许删除；
2. 返回 409，提示该分类已被资产使用；
3. 建议使用停用状态代替删除。
```

---

# 8. 资产管理 Asset API

## 8.1 查询资产列表

```http
GET /api/v1/assets
```

权限：admin、it_staff

查询参数：

| 参数          | 类型     | 必填 | 说明                                   |
| ----------- | ------ | -- | ------------------------------------ |
| keyword     | string | 否  | 资产编号、资产名称、品牌、型号、序列号                  |
| category_id | int    | 否  | 资产分类ID                               |
| status      | string | 否  | in_use / idle / repairing / scrapped |
| department  | string | 否  | 所属部门                                 |
| user_id     | int    | 否  | 使用人ID                                |
| page        | int    | 否  | 页码                                   |
| page_size   | int    | 否  | 每页数量                                 |

请求示例：

```http
GET /api/v1/assets?keyword=电脑&status=in_use&page=1&page_size=10
```

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "asset_no": "IT-PC-2026-0001",
        "asset_name": "财务部办公电脑",
        "category_id": 1,
        "category_name": "办公电脑",
        "brand": "Dell",
        "model": "OptiPlex 7090",
        "serial_no": "SN-PC-0001",
        "user_id": 3,
        "user_name": "李明",
        "department": "财务部",
        "location": "财务办公室A区",
        "status": "in_use",
        "purchase_date": "2024-05-10",
        "warranty_expire_date": "2027-05-10"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "pages": 1
  }
}
```

---

## 8.2 创建资产

```http
POST /api/v1/assets
```

权限：admin

请求参数：

```json
{
  "asset_no": "IT-PC-2026-0004",
  "asset_name": "招商部办公电脑",
  "category_id": 1,
  "brand": "Lenovo",
  "model": "ThinkCentre M750",
  "serial_no": "SN-PC-0004",
  "user_id": 5,
  "department": "招商部",
  "location": "招商办公室C区",
  "status": "in_use",
  "purchase_date": "2025-01-10",
  "warranty_expire_date": "2028-01-10",
  "remark": "招商部员工办公电脑"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "资产创建成功",
  "data": {
    "id": 4,
    "asset_no": "IT-PC-2026-0004"
  }
}
```

业务规则：

```text
1. asset_no 不允许重复；
2. category_id 必须存在；
3. user_id 如果传入，必须存在；
4. status 必须为合法枚举值；
5. 创建成功后记录操作日志。
```

---

## 8.3 查询资产详情

```http
GET /api/v1/assets/{asset_id}
```

权限：admin、it_staff

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "asset_no": "IT-PC-2026-0001",
    "asset_name": "财务部办公电脑",
    "category_id": 1,
    "category_name": "办公电脑",
    "brand": "Dell",
    "model": "OptiPlex 7090",
    "serial_no": "SN-PC-0001",
    "user_id": 3,
    "user_name": "李明",
    "department": "财务部",
    "location": "财务办公室A区",
    "status": "in_use",
    "purchase_date": "2024-05-10",
    "warranty_expire_date": "2027-05-10",
    "remark": "财务部日常办公电脑",
    "created_at": "2026-06-21 08:00:00",
    "updated_at": "2026-06-21 08:00:00"
  }
}
```

---

## 8.4 修改资产

```http
PUT /api/v1/assets/{asset_id}
```

权限：admin

请求参数：

```json
{
  "asset_name": "财务部办公电脑",
  "category_id": 1,
  "brand": "Dell",
  "model": "OptiPlex 7090",
  "serial_no": "SN-PC-0001",
  "user_id": 3,
  "department": "财务部",
  "location": "财务办公室A区",
  "status": "in_use",
  "purchase_date": "2024-05-10",
  "warranty_expire_date": "2027-05-10",
  "remark": "财务部日常办公电脑"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "资产修改成功",
  "data": null
}
```

业务规则：

```text
1. 不允许通过该接口修改 asset_no；
2. 如果资产存在 processing 状态的未完成工单，不建议直接改为 scrapped；
3. 修改成功后记录操作日志。
```

---

## 8.5 修改资产状态

```http
PATCH /api/v1/assets/{asset_id}/status
```

权限：admin、it_staff

请求参数：

```json
{
  "status": "repairing",
  "remark": "该资产正在维修"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "资产状态修改成功",
  "data": null
}
```

业务规则：

```text
1. status 必须是 in_use、idle、repairing、scrapped 之一；
2. 工单开始处理时，可自动将资产状态改为 repairing；
3. 工单完成后，可根据维修结果改为 in_use 或 scrapped；
4. 修改后记录操作日志。
```

---

## 8.6 删除资产

```http
DELETE /api/v1/assets/{asset_id}
```

权限：admin

成功响应：

```json
{
  "code": 0,
  "message": "资产删除成功",
  "data": null
}
```

业务规则：

```text
1. 如果资产已关联工单或维修记录，不允许物理删除；
2. 返回 409，提示该资产已有业务记录；
3. 建议将资产状态改为 scrapped。
```

---

## 8.7 查询资产维修历史

```http
GET /api/v1/assets/{asset_id}/repair-records
```

权限：admin、it_staff

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "ticket_id": 1,
      "ticket_no": "TK202606210001",
      "ticket_title": "财务电脑无法开机",
      "repair_user_id": 2,
      "repair_user_name": "张工",
      "fault_reason": "内存接触不良，主机内部灰尘较多",
      "repair_method": "重新插拔内存条并清理机箱灰尘",
      "repair_result": "fixed",
      "repair_cost": 0.0,
      "repaired_at": "2026-06-21 10:10:00"
    }
  ]
}
```

---

# 9. 报修工单 Ticket API

## 9.1 查询工单列表

```http
GET /api/v1/tickets
```

权限：admin、it_staff、employee

查询参数：

| 参数          | 类型     | 必填 | 说明                                                        |
| ----------- | ------ | -- | --------------------------------------------------------- |
| keyword     | string | 否  | 工单编号、标题、描述                                                |
| status      | string | 否  | pending / assigned / processing / completed / cancelled   |
| priority    | string | 否  | low / normal / high / urgent                              |
| fault_type  | string | 否  | hardware / software / network / printer / account / other |
| reporter_id | int    | 否  | 报修人ID                                                     |
| handler_id  | int    | 否  | 处理人ID                                                     |
| asset_id    | int    | 否  | 资产ID                                                      |
| start_date  | string | 否  | 创建开始日期，格式 YYYY-MM-DD                                      |
| end_date    | string | 否  | 创建结束日期，格式 YYYY-MM-DD                                      |
| page        | int    | 否  | 页码                                                        |
| page_size   | int    | 否  | 每页数量                                                      |

权限过滤规则：

```text
1. admin 可以查看全部工单；
2. it_staff 可以查看全部工单；
3. employee 只能查看 reporter_id = 当前用户ID 的工单。
```

请求示例：

```http
GET /api/v1/tickets?status=pending&page=1&page_size=10
```

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "ticket_no": "TK202606210001",
        "title": "财务电脑无法开机",
        "fault_type": "hardware",
        "priority": "high",
        "status": "completed",
        "reporter_id": 3,
        "reporter_name": "李明",
        "handler_id": 2,
        "handler_name": "张工",
        "asset_id": 1,
        "asset_no": "IT-PC-2026-0001",
        "asset_name": "财务部办公电脑",
        "created_at": "2026-06-21 09:10:00",
        "completed_at": "2026-06-21 10:10:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "pages": 1
  }
}
```

---

## 9.2 创建报修工单

```http
POST /api/v1/tickets
```

权限：employee、admin、it_staff

请求参数：

```json
{
  "title": "办公电脑无法开机",
  "description": "按下电源键后主机没有反应，显示器无信号。",
  "fault_type": "hardware",
  "priority": "high",
  "asset_id": 1
}
```

字段说明：

| 字段          | 类型     | 必填 | 说明            |
| ----------- | ------ | -- | ------------- |
| title       | string | 是  | 工单标题          |
| description | string | 是  | 故障描述          |
| fault_type  | string | 是  | 故障类型          |
| priority    | string | 否  | 优先级，默认 normal |
| asset_id    | int    | 否  | 关联资产ID        |

成功响应：

```json
{
  "code": 0,
  "message": "工单创建成功",
  "data": {
    "id": 5,
    "ticket_no": "TK202606230001",
    "status": "pending"
  }
}
```

业务规则：

```text
1. ticket_no 由后端自动生成，格式：TK + yyyyMMdd + 4位序号，例如 TK202606230001；
2. reporter_id 使用当前登录用户ID；
3. 创建后 status = pending；
4. 如果 asset_id 传入，必须校验资产是否存在；
5. 创建成功后写入 it_ticket_record，action = create；
6. 创建成功后记录操作日志。
```

---

## 9.3 查询工单详情

```http
GET /api/v1/tickets/{ticket_id}
```

权限：admin、it_staff、工单报修人本人

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "ticket_no": "TK202606210001",
    "title": "财务电脑无法开机",
    "description": "按下电源键后电脑无反应，显示器无信号。",
    "fault_type": "hardware",
    "priority": "high",
    "status": "completed",
    "reporter": {
      "id": 3,
      "real_name": "李明",
      "department": "财务部",
      "phone": "13800000003"
    },
    "handler": {
      "id": 2,
      "real_name": "张工",
      "department": "信息部",
      "phone": "13800000002"
    },
    "asset": {
      "id": 1,
      "asset_no": "IT-PC-2026-0001",
      "asset_name": "财务部办公电脑",
      "brand": "Dell",
      "model": "OptiPlex 7090",
      "location": "财务办公室A区"
    },
    "result": "重新插拔内存并清理主板灰尘后恢复正常。",
    "created_at": "2026-06-21 09:10:00",
    "assigned_at": "2026-06-21 09:20:00",
    "started_at": "2026-06-21 09:30:00",
    "completed_at": "2026-06-21 10:10:00",
    "records": [
      {
        "id": 1,
        "operator_id": 3,
        "operator_name": "李明",
        "from_status": null,
        "to_status": "pending",
        "action": "create",
        "remark": "用户提交电脑无法开机工单",
        "created_at": "2026-06-21 09:10:00"
      }
    ]
  }
}
```

---

## 9.4 修改工单基础信息

```http
PUT /api/v1/tickets/{ticket_id}
```

权限：admin、工单报修人本人

请求参数：

```json
{
  "title": "办公电脑无法开机",
  "description": "按下电源键后主机没有反应，显示器无信号。",
  "fault_type": "hardware",
  "priority": "high",
  "asset_id": 1
}
```

成功响应：

```json
{
  "code": 0,
  "message": "工单修改成功",
  "data": null
}
```

业务规则：

```text
1. 只有 pending 状态的工单允许报修人修改；
2. admin 可以修改 pending、assigned 状态工单；
3. processing、completed、cancelled 状态不允许修改基础信息；
4. 修改后记录操作日志。
```

---

## 9.5 派单

```http
PATCH /api/v1/tickets/{ticket_id}/assign
```

权限：admin

请求参数：

```json
{
  "handler_id": 2,
  "remark": "派给张工处理"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "派单成功",
  "data": {
    "id": 1,
    "status": "assigned",
    "handler_id": 2,
    "assigned_at": "2026-06-23 10:00:00"
  }
}
```

业务规则：

```text
1. 只有 pending 状态允许派单；
2. handler_id 对应用户必须存在；
3. handler 用户 role 必须为 it_staff 或 admin；
4. 派单后 status = assigned；
5. 更新 handler_id、assigned_at；
6. 写入 it_ticket_record，action = assign；
7. 记录操作日志。
```

---

## 9.6 接单并开始处理

```http
PATCH /api/v1/tickets/{ticket_id}/start
```

权限：admin、it_staff

请求参数：

```json
{
  "remark": "开始排查故障"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "工单已开始处理",
  "data": {
    "id": 1,
    "status": "processing",
    "started_at": "2026-06-23 10:15:00"
  }
}
```

业务规则：

```text
1. assigned 状态允许开始处理；
2. it_staff 只能开始处理分配给自己的工单；
3. admin 可以开始处理任意 assigned 工单；
4. 如果工单 handler_id 为空，IT 人员开始处理时自动设置 handler_id = 当前用户ID；
5. 开始处理后 status = processing；
6. 更新 started_at；
7. 如果工单关联了 asset_id，则将资产状态改为 repairing；
8. 写入 it_ticket_record，action = start；
9. 记录操作日志。
```

---

## 9.7 完成工单

```http
PATCH /api/v1/tickets/{ticket_id}/complete
```

权限：admin、工单处理人本人

请求参数：

```json
{
  "result": "重新插拔内存并清理机箱灰尘后恢复正常。",
  "fault_reason": "内存接触不良，主机内部灰尘较多",
  "repair_method": "重新插拔内存条并清理机箱灰尘",
  "repair_result": "fixed",
  "repair_cost": 0.0,
  "asset_status_after_repair": "in_use",
  "remark": "工单处理完成"
}
```

字段说明：

| 字段                        | 类型     | 必填 | 说明                                             |
| ------------------------- | ------ | -- | ---------------------------------------------- |
| result                    | string | 是  | 工单处理结果                                         |
| fault_reason              | string | 否  | 故障原因                                           |
| repair_method             | string | 否  | 维修方法                                           |
| repair_result             | string | 是  | fixed / replace_repair / scrapped / unresolved |
| repair_cost               | number | 否  | 维修费用                                           |
| asset_status_after_repair | string | 否  | in_use / repairing / scrapped                  |
| remark                    | string | 否  | 流转备注                                           |

成功响应：

```json
{
  "code": 0,
  "message": "工单已完成",
  "data": {
    "id": 1,
    "status": "completed",
    "completed_at": "2026-06-23 11:00:00"
  }
}
```

业务规则：

```text
1. 只有 processing 状态允许完成；
2. it_staff 只能完成自己处理的工单；
3. admin 可以完成任意 processing 工单；
4. 完成后 status = completed；
5. 更新 result、completed_at；
6. 如果工单关联 asset_id：
   - 创建 it_repair_record 维修记录；
   - 根据 asset_status_after_repair 更新资产状态；
   - 如果 repair_result = fixed 或 replace_repair，默认资产状态改为 in_use；
   - 如果 repair_result = scrapped，资产状态改为 scrapped；
   - 如果 repair_result = unresolved，资产状态保持 repairing；
7. 写入 it_ticket_record，action = finish；
8. 记录操作日志。
```

---

## 9.8 取消工单

```http
PATCH /api/v1/tickets/{ticket_id}/cancel
```

权限：admin、工单报修人本人

请求参数：

```json
{
  "reason": "问题已自行解决，不需要处理"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "工单已取消",
  "data": {
    "id": 1,
    "status": "cancelled"
  }
}
```

业务规则：

```text
1. 只有 pending 状态允许报修人取消；
2. admin 可以取消 pending、assigned 状态工单；
3. processing、completed 状态不允许取消；
4. 取消后 status = cancelled；
5. 写入 it_ticket_record，action = cancel；
6. 记录操作日志。
```

---

## 9.9 删除工单

```http
DELETE /api/v1/tickets/{ticket_id}
```

权限：admin

成功响应：

```json
{
  "code": 0,
  "message": "工单删除成功",
  "data": null
}
```

业务规则：

```text
1. 第一版建议不做物理删除；
2. 如果必须实现，只允许删除 pending 或 cancelled 状态工单；
3. 如果已有维修记录，不允许删除；
4. 推荐通过 cancelled 状态代替删除。
```

---

# 10. 工单流转记录 Ticket Record API

## 10.1 查询指定工单流转记录

```http
GET /api/v1/tickets/{ticket_id}/records
```

权限：admin、it_staff、工单报修人本人

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "ticket_id": 1,
      "operator_id": 3,
      "operator_name": "李明",
      "from_status": null,
      "to_status": "pending",
      "action": "create",
      "remark": "用户提交电脑无法开机工单",
      "created_at": "2026-06-21 09:10:00"
    },
    {
      "id": 2,
      "ticket_id": 1,
      "operator_id": 1,
      "operator_name": "系统管理员",
      "from_status": "pending",
      "to_status": "assigned",
      "action": "assign",
      "remark": "管理员将工单派给张工处理",
      "created_at": "2026-06-21 09:20:00"
    }
  ]
}
```

业务规则：

```text
1. 流转记录只允许查询，不提供手动新增、修改、删除接口；
2. 记录由工单业务接口自动写入。
```

---

# 11. 维修记录 Repair Record API

## 11.1 查询维修记录列表

```http
GET /api/v1/repair-records
```

权限：admin、it_staff

查询参数：

| 参数             | 类型     | 必填 | 说明     |
| -------------- | ------ | -- | ------ |
| asset_id       | int    | 否  | 资产ID   |
| ticket_id      | int    | 否  | 工单ID   |
| repair_user_id | int    | 否  | 维修人员ID |
| repair_result  | string | 否  | 维修结果   |
| start_date     | string | 否  | 维修开始日期 |
| end_date       | string | 否  | 维修结束日期 |
| page           | int    | 否  | 页码     |
| page_size      | int    | 否  | 每页数量   |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "ticket_id": 1,
        "ticket_no": "TK202606210001",
        "ticket_title": "财务电脑无法开机",
        "asset_id": 1,
        "asset_no": "IT-PC-2026-0001",
        "asset_name": "财务部办公电脑",
        "repair_user_id": 2,
        "repair_user_name": "张工",
        "fault_reason": "内存接触不良，主机内部灰尘较多",
        "repair_method": "重新插拔内存条并清理机箱灰尘",
        "repair_result": "fixed",
        "repair_cost": 0.0,
        "repaired_at": "2026-06-21 10:10:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "pages": 1
  }
}
```

业务规则：

```text
1. 维修记录主要由完成工单接口自动生成；
2. 第一版不提供手动创建维修记录接口；
3. 如需修改维修记录，只允许 admin 修改。
```

---

## 11.2 查询维修记录详情

```http
GET /api/v1/repair-records/{record_id}
```

权限：admin、it_staff

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "ticket_id": 1,
    "ticket_no": "TK202606210001",
    "asset_id": 1,
    "asset_no": "IT-PC-2026-0001",
    "asset_name": "财务部办公电脑",
    "repair_user_id": 2,
    "repair_user_name": "张工",
    "fault_reason": "内存接触不良，主机内部灰尘较多",
    "repair_method": "重新插拔内存条并清理机箱灰尘",
    "repair_result": "fixed",
    "repair_cost": 0.0,
    "repaired_at": "2026-06-21 10:10:00",
    "created_at": "2026-06-21 10:10:00"
  }
}
```

---

## 11.3 修改维修记录

```http
PUT /api/v1/repair-records/{record_id}
```

权限：admin

请求参数：

```json
{
  "fault_reason": "内存接触不良",
  "repair_method": "重新插拔内存并清理灰尘",
  "repair_result": "fixed",
  "repair_cost": 0.0,
  "repaired_at": "2026-06-21 10:10:00"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "维修记录修改成功",
  "data": null
}
```

---

# 12. 操作日志 Operation Log API

## 12.1 查询操作日志列表

```http
GET /api/v1/operation-logs
```

权限：admin

查询参数：

| 参数               | 类型     | 必填 | 说明             |
| ---------------- | ------ | -- | -------------- |
| user_id          | int    | 否  | 操作用户ID         |
| module_name      | string | 否  | 模块名称           |
| operation_type   | string | 否  | 操作类型           |
| operation_result | string | 否  | success / fail |
| start_date       | string | 否  | 开始日期           |
| end_date         | string | 否  | 结束日期           |
| page             | int    | 否  | 页码             |
| page_size        | int    | 否  | 每页数量           |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "username": "admin",
        "real_name": "系统管理员",
        "module_name": "用户登录",
        "operation_type": "login",
        "business_id": null,
        "request_method": "POST",
        "request_url": "/api/v1/auth/login",
        "request_ip": "192.168.1.10",
        "operation_result": "success",
        "error_message": null,
        "created_at": "2026-06-21 08:50:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "pages": 1
  }
}
```

业务规则：

```text
1. 操作日志由系统自动写入；
2. 第一版不提供新增、修改、删除日志接口；
3. 登录、创建工单、修改工单状态、创建资产、修改资产等关键操作都应记录日志。
```

---

# 13. 首页统计 Dashboard API

## 13.1 查询首页统计卡片

```http
GET /api/v1/dashboard/summary
```

权限：admin、it_staff

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ticket_total": 128,
    "ticket_pending": 12,
    "ticket_processing": 8,
    "ticket_completed": 100,
    "asset_total": 86,
    "asset_in_use": 70,
    "asset_repairing": 5,
    "asset_scrapped": 3
  }
}
```

统计规则：

```text
ticket_total：工单总数
ticket_pending：pending 状态工单数量
ticket_processing：processing 状态工单数量
ticket_completed：completed 状态工单数量
asset_total：资产总数
asset_in_use：in_use 状态资产数量
asset_repairing：repairing 状态资产数量
asset_scrapped：scrapped 状态资产数量
```

---

## 13.2 查询最近 7 天工单趋势

```http
GET /api/v1/dashboard/ticket-trend
```

权限：admin、it_staff

查询参数：

| 参数   | 类型  | 必填 | 说明               |
| ---- | --- | -- | ---------------- |
| days | int | 否  | 最近多少天，默认 7，最大 30 |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "date": "2026-06-17",
      "count": 5
    },
    {
      "date": "2026-06-18",
      "count": 8
    },
    {
      "date": "2026-06-19",
      "count": 3
    }
  ]
}
```

统计规则：

```text
按照 it_ticket.created_at 的日期分组统计。
```

---

## 13.3 查询工单类型分布

```http
GET /api/v1/dashboard/ticket-fault-types
```

权限：admin、it_staff

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "fault_type": "hardware",
      "fault_type_name": "硬件故障",
      "count": 20
    },
    {
      "fault_type": "network",
      "fault_type_name": "网络故障",
      "count": 15
    }
  ]
}
```

---

## 13.4 查询资产状态分布

```http
GET /api/v1/dashboard/asset-status
```

权限：admin、it_staff

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "status": "in_use",
      "status_name": "在用",
      "count": 70
    },
    {
      "status": "repairing",
      "status_name": "维修中",
      "count": 5
    }
  ]
}
```

---

## 13.5 查询运维人员处理排行

```http
GET /api/v1/dashboard/handler-ranking
```

权限：admin、it_staff

查询参数：

| 参数         | 类型     | 必填 | 说明         |
| ---------- | ------ | -- | ---------- |
| start_date | string | 否  | 开始日期       |
| end_date   | string | 否  | 结束日期       |
| limit      | int    | 否  | 返回数量，默认 10 |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "handler_id": 2,
      "handler_name": "张工",
      "completed_count": 36
    }
  ]
}
```

统计规则：

```text
统计 completed 状态工单，按照 handler_id 分组。
```

---

# 14. 字典接口 Dict API

为了方便前端渲染下拉框，提供统一字典接口。

## 14.1 查询所有字典

```http
GET /api/v1/dicts
```

权限：登录用户

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "roles": [
      {
        "label": "管理员",
        "value": "admin"
      },
      {
        "label": "IT运维人员",
        "value": "it_staff"
      },
      {
        "label": "普通员工",
        "value": "employee"
      }
    ],
    "ticket_status": [
      {
        "label": "待受理",
        "value": "pending"
      },
      {
        "label": "已派单",
        "value": "assigned"
      },
      {
        "label": "处理中",
        "value": "processing"
      },
      {
        "label": "已完成",
        "value": "completed"
      },
      {
        "label": "已取消",
        "value": "cancelled"
      }
    ],
    "ticket_priority": [
      {
        "label": "低",
        "value": "low"
      },
      {
        "label": "普通",
        "value": "normal"
      },
      {
        "label": "高",
        "value": "high"
      },
      {
        "label": "紧急",
        "value": "urgent"
      }
    ],
    "fault_type": [
      {
        "label": "硬件故障",
        "value": "hardware"
      },
      {
        "label": "软件故障",
        "value": "software"
      },
      {
        "label": "网络故障",
        "value": "network"
      },
      {
        "label": "打印机故障",
        "value": "printer"
      },
      {
        "label": "账号权限问题",
        "value": "account"
      },
      {
        "label": "其他",
        "value": "other"
      }
    ],
    "asset_status": [
      {
        "label": "在用",
        "value": "in_use"
      },
      {
        "label": "闲置",
        "value": "idle"
      },
      {
        "label": "维修中",
        "value": "repairing"
      },
      {
        "label": "已报废",
        "value": "scrapped"
      }
    ]
  }
}
```

---

# 15. 工单状态流转规则

工单状态只能按照以下规则流转：

```text
pending    -> assigned
pending    -> cancelled
assigned   -> processing
assigned   -> cancelled
processing -> completed
```

禁止：

```text
completed  -> 任意状态
cancelled  -> 任意状态
pending    -> completed
assigned   -> completed
processing -> cancelled
```

如果状态流转非法，返回：

```json
{
  "code": 40900,
  "message": "当前工单状态不允许执行该操作",
  "data": null
}
```

---

# 16. 后端实现要求

## 16.1 FastAPI 路由建议

建议拆分以下 router：

```text
app/api/v1/routers/auth.py
app/api/v1/routers/users.py
app/api/v1/routers/assets.py
app/api/v1/routers/asset_categories.py
app/api/v1/routers/tickets.py
app/api/v1/routers/repair_records.py
app/api/v1/routers/operation_logs.py
app/api/v1/routers/dashboard.py
app/api/v1/routers/dicts.py
```

---

## 16.2 Service 层建议

建议拆分以下 service：

```text
app/services/auth_service.py
app/services/user_service.py
app/services/asset_service.py
app/services/ticket_service.py
app/services/repair_service.py
app/services/log_service.py
app/services/dashboard_service.py
```

---

## 16.3 数据模型建议

建议拆分以下 model：

```text
app/models/user.py
app/models/asset_category.py
app/models/asset.py
app/models/ticket.py
app/models/ticket_record.py
app/models/repair_record.py
app/models/operation_log.py
```

---

## 16.4 Pydantic Schema 建议

建议拆分以下 schema：

```text
app/schemas/auth_schema.py
app/schemas/user_schema.py
app/schemas/asset_schema.py
app/schemas/ticket_schema.py
app/schemas/repair_schema.py
app/schemas/common_schema.py
```

---

## 16.5 统一响应工具

请封装统一响应方法：

```python
def success(data=None, message="success"):
    return {
        "code": 0,
        "message": message,
        "data": data
    }

def fail(code=40000, message="操作失败", data=None):
    return {
        "code": code,
        "message": message,
        "data": data
    }
```

---

## 16.6 权限校验要求

需要实现依赖函数：

```text
get_current_user
require_roles
```

示例：

```text
require_roles("admin")
require_roles("admin", "it_staff")
```

---

## 16.7 操作日志要求

以下操作必须写入 sys_operation_log：

```text
用户登录
创建用户
修改用户
禁用用户
创建资产
修改资产
修改资产状态
创建工单
修改工单
派单
开始处理
完成工单
取消工单
修改维修记录
```

日志字段：

```text
user_id
module_name
operation_type
business_id
request_method
request_url
request_ip
operation_result
error_message
created_at
```

---

# 17. 第一版必须实现的接口清单

Codex 第一阶段必须完整实现以下接口：

```text
POST   /api/v1/auth/login
GET    /api/v1/auth/me
PUT    /api/v1/auth/password

GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{user_id}
PUT    /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}/status
PATCH  /api/v1/users/{user_id}/password
DELETE /api/v1/users/{user_id}

GET    /api/v1/asset-categories
POST   /api/v1/asset-categories
GET    /api/v1/asset-categories/{category_id}
PUT    /api/v1/asset-categories/{category_id}
DELETE /api/v1/asset-categories/{category_id}

GET    /api/v1/assets
POST   /api/v1/assets
GET    /api/v1/assets/{asset_id}
PUT    /api/v1/assets/{asset_id}
PATCH  /api/v1/assets/{asset_id}/status
DELETE /api/v1/assets/{asset_id}
GET    /api/v1/assets/{asset_id}/repair-records

GET    /api/v1/tickets
POST   /api/v1/tickets
GET    /api/v1/tickets/{ticket_id}
PUT    /api/v1/tickets/{ticket_id}
PATCH  /api/v1/tickets/{ticket_id}/assign
PATCH  /api/v1/tickets/{ticket_id}/start
PATCH  /api/v1/tickets/{ticket_id}/complete
PATCH  /api/v1/tickets/{ticket_id}/cancel
DELETE /api/v1/tickets/{ticket_id}
GET    /api/v1/tickets/{ticket_id}/records

GET    /api/v1/repair-records
GET    /api/v1/repair-records/{record_id}
PUT    /api/v1/repair-records/{record_id}

GET    /api/v1/operation-logs

GET    /api/v1/dashboard/summary
GET    /api/v1/dashboard/ticket-trend
GET    /api/v1/dashboard/ticket-fault-types
GET    /api/v1/dashboard/asset-status
GET    /api/v1/dashboard/handler-ranking

GET    /api/v1/dicts
```

---

# 18. Codex 实现补充要求

请 Codex 按以下要求实现：

```text
1. 使用 FastAPI 实现所有接口；
2. 使用 SQLAlchemy ORM 操作 MySQL；
3. 使用 Pydantic 定义请求和响应 Schema；
4. 所有接口统一返回 code、message、data；
5. 登录使用 JWT Token；
6. 密码必须使用安全哈希存储，不允许明文保存；
7. 所有列表接口必须支持分页；
8. 查询接口需要支持文档中定义的过滤条件；
9. 所有涉及业务状态变更的接口必须校验状态流转是否合法；
10. 所有关键操作必须写入 sys_operation_log；
11. 报修工单创建、派单、开始处理、完成、取消时必须写入 it_ticket_record；
12. 完成工单时，如果有关联资产，必须自动创建 it_repair_record；
13. 完成工单时，需要根据维修结果自动更新资产状态；
14. 普通员工只能查看和操作自己的工单；
15. IT 运维人员不能管理用户；
16. 管理员拥有全部权限；
17. 代码结构需要分层：routers、services、models、schemas、utils；
18. 接口需要能在 /docs 中正常显示；
19. 所有接口需要有合理的异常处理；
20. 不要把业务逻辑全部写在 router 中，核心逻辑放在 service 层。
```
