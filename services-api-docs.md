# 🐕 社区服务板块 — 前端对接文档

> 所有接口统一前缀：`http://127.0.0.1:8000`
> Content-Type: `application/json`（图片上传使用 `form-data`）

---

## 通用规则

**Header 必传**

| Header | 必填 | 说明 |
|---|---|---|
| `X-App-Code` | ✅ | 固定传 `doxie` |
| `Authorization` | ⚠️ 部分接口需要 | `Bearer <token>` |

**统一响应格式**

```json
{ "code": 0, "message": "success", "data": {} }
```

**分页返回结构**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [],
    "total": 10,
    "total_page": 1,
    "page": 1,
    "page_size": 12
  }
}
```

---

## 分类与费用枚举

**分类 (category)**

| 值 | 展示 |
|---|---|
| `walking` | 遛狗陪伴 |
| `veterinary` | 兽医咨询 |
| `boarding` | 宠物寄养 |
| `grooming` | 洗澡美容 |
| `lost_found` | 寻狗/捡狗 |
| `meetup` | 狗友组局 |
| `other` | 其它 |

**费用类型 (fee_type)**

| 值 | 展示 |
|---|---|
| `free` | 免费 |
| `negotiable` | 面议 |
| `paid` | 收费 |

---

## 接口列表

### 1. 创建服务

发布一条社区服务。

```
POST /api/services
```

**需要登录** ✅ — Header 需携带 `Authorization: Bearer <token>`

**请求体**

```json
{
  "category": "walking",
  "title": "周末东湖遛狗",
  "description": "每周末下午可以帮忙遛狗，本人养狗5年经验...",
  "contact_phone": "13800138000",
  "contact_wechat": "dogwalker123",
  "service_area": "东湖附近",
  "available_time": "周六日下午 2-6 点",
  "fee_type": "free",
  "provider_image": null
}
```

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| category | string | ✅ | 必须是上述 7 种分类之一 |
| title | string | ✅ | 1-100 字 |
| description | string | ✅ | 服务详细介绍 |
| contact_phone | string | ⚠️ | phone 和 wechat **至少填一个** |
| contact_wechat | string | ⚠️ | phone 和 wechat **至少填一个** |
| service_area | string |  | 服务区域，建议填 |
| available_time | string |  | 可服务时间，建议填 |
| fee_type | string | ✅ | `free` / `negotiable` / `paid`，默认 `free` |
| provider_image | string |  | 服务者头像 URL，可先上传再填入 |

**成功响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "user_id": "用户ID",
    "app_code": "doxie",
    "category": "walking",
    "title": "周末东湖遛狗",
    "description": "每周末下午可以帮忙遛狗...",
    "contact_phone": "13800138000",
    "contact_wechat": "dogwalker123",
    "service_area": "东湖附近",
    "available_time": "周六日下午 2-6 点",
    "fee_type": "free",
    "is_verified": false,
    "provider_image": null,
    "status": 0,
    "is_deleted": false,
    "created_at": "2026-04-15T12:00:00+00:00",
    "updated_at": "2026-04-15T12:00:00+00:00"
  }
}
```

**失败场景**

| code | message | 说明 |
|---|---|---|
| 400 | "Invalid category. Must be one of: ..." | 分类不存在 |
| 400 | "Invalid fee_type. Must be one of: ..." | 费用类型不合法 |
| 400 | "At least one contact method is required" | 未填任何联系方式 |
| 401 | "token invalid / token expired" | 未登录或 token 过期 |

---

### 2. 获取服务列表（公开）

浏览广场上的所有服务，支持按分类筛选。

```
GET /api/services?page=1&page_size=12&category=walking
```

**不需要登录** ❌

| 参数 | 必填 | 说明 |
|---|---|---|
| page |  | 页码，默认 `1` |
| page_size |  | 每页条数，默认 `12`，最大 `50` |
| category |  | 筛选分类，不传则返回全部 |

> ⚠️ 列表接口**不返回**联系方式（phone / wechat）
> ⚠️ 只返回 `status=0`（正常展示）且 `is_deleted=false` 的记录
> ⚠️ description 超过 120 字自动截断加 `…`

**成功响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "uuid",
        "user_id": "用户ID",
        "nickname": "DOXIE_aB3x",
        "category": "walking",
        "title": "周末东湖遛狗",
        "description": "每周末下午可以帮忙遛狗，本人养狗5年经验...",
        "service_area": "东湖附近",
        "fee_type": "free",
        "is_verified": false,
        "provider_image": "https://xxx.supabase.co/...",
        "created_at": "2026-04-15T12:00:00+00:00"
      }
    ],
    "total": 10,
    "total_page": 1,
    "page": 1,
    "page_size": 12
  }
}
```

| 返回字段 | 类型 | 说明 |
|---|---|---|
| nickname | string | 发布者的昵称（从用户表关联） |
| is_verified | bool | 平台认证标记，未认证时 `false` |
| description | string | 超过120字自动截断 |
| provider_image | string / null | 服务者头像 URL，列表卡片展示用 |

---

### 3. 获取我的服务列表

查看当前登录用户自己发布的所有服务。

```
GET /api/services/mine?page=1&page_size=12
```

**需要登录** ✅ — Header 需携带 `Authorization: Bearer <token>`

⚠️ 注意路径是 `/mine`，不是 `/{user_id}`。从 token 自动识别当前用户。

**成功响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "uuid",
        "user_id": "当前用户ID",
        "category": "walking",
        "title": "周末东湖遛狗",
        "description": "每周末下午可以帮忙遛狗...",
        "service_area": "东湖附近",
        "fee_type": "free",
        "is_verified": false,
        "status": 0,
        "provider_image": "https://xxx.supabase.co/...",
        "created_at": "2026-04-15T12:00:00+00:00"
      }
    ],
    "total": 3,
    "total_page": 1,
    "page": 1,
    "page_size": 12
  }
}
```

> 我的列表比公开列表多一个 `status` 字段，方便查看已下架的服务。

---

### 4. 获取服务详情

查看某条服务的完整信息。

```
GET /api/services/{service_id}
```

**不需要登录** ❌，但**登录后可看到联系方式**

- 未登录 / token 无效：`contact_phone` 和 `contact_wechat` 返回 `null`
- 已登录（带有效 token）：返回完整联系方式

**请求示例**

```
GET /api/services/xxx-xxx-xxx
Header:
  X-App-Code: doxie
  Authorization: Bearer <token>   ← 可选，不传也能看到内容
```

**成功响应（已登录）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "service": {
      "id": "uuid",
      "user_id": "用户ID",
      "nickname": "DOXIE_aB3x",
      "avatar": "https://www.kaoiki.com/default.webp",
      "category": "walking",
      "title": "周末东湖遛狗",
      "description": "每周末下午可以帮忙遛狗，本人养狗5年经验...",
      "contact_phone": "13800138000",
      "contact_wechat": "dogwalker123",
      "service_area": "东湖附近",
      "available_time": "周六日下午 2-6 点",
      "fee_type": "free",
      "is_verified": false,
      "provider_image": "https://xxx.supabase.co/...",
      "service_images": [
        { "id": "img-uuid", "path": "services/xxx/yyy.jpg", "url": "https://xxx.supabase.co/..." }
      ],
      "service_image_count": 1,
      "is_owner": false,
      "created_at": "2026-04-15T12:00:00+00:00",
      "updated_at": "2026-04-15T12:00:00+00:00"
    }
  }
}
```

**成功响应（未登录 / token 无效）** — contact 字段为 `null`

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "service": {
      "id": "uuid",
      "user_id": "用户ID",
      "nickname": "DOXIE_aB3x",
      "avatar": "https://www.kaoiki.com/default.webp",
      "category": "walking",
      "title": "周末东湖遛狗",
      "description": "每周末下午可以帮忙遛狗，本人养狗5年经验...",
      "contact_phone": null,
      "contact_wechat": null,
      "service_area": "东湖附近",
      "available_time": "周六日下午 2-6 点",
      "fee_type": "free",
      "is_verified": false,
      "provider_image": "https://xxx.supabase.co/...",
      "service_images": [
        { "id": "img-uuid", "path": "services/xxx/yyy.jpg", "url": "https://xxx.supabase.co/..." }
      ],
      "service_image_count": 1,
      "is_owner": false,
      "created_at": "2026-04-15T12:00:00+00:00",
      "updated_at": "2026-04-15T12:00:00+00:00"
    }
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| nickname | string | 发布者昵称 |
| avatar | string | 发布者头像 URL（用户表头像） |
| provider_image | string / null | 服务者展示头像，和 user 头像不同 |
| service_images | array | 资质佐证图列表，每项含 `{id, path, url}` |
| service_image_count | int | 资质佐证图数量 |
| is_owner | bool | 当前登录用户是否是发布者（用于显示编辑/删除按钮） |
| contact_phone | string / null | 未登录时为 `null` |
| contact_wechat | string / null | 未登录时为 `null` |
| is_verified | bool | 平台认证标记，默认 `false` |

---

### 5. 更新服务

修改已发布的服务信息。只传需要修改的字段即可。

```
PUT /api/services/{service_id}
```

**需要登录** ✅ — 仅该服务的创建者可操作

**请求体（全部可选，只传要改的字段）**

```json
{
  "title": "更新后的标题",
  "fee_type": "negotiable",
  "contact_wechat": "new_wechat_id",
  "provider_image": "https://xxx.supabase.co/new-image.jpg"
}
```

> 如果修改联系方式，仍然不能同时把 phone 和 wechat 都置空。

**成功响应** — 返回更新后的完整服务对象（同详情接口结构）

**失败场景**

| code | message | 说明 |
|---|---|---|
| 403 | "Forbidden" | 不是该服务的创建者 |
| 404 | "Service not found" | 服务不存在 |
| 400 | "No fields to update" | 请求体为空 |

---

### 6. 删除服务（下架）

```
DELETE /api/services/{service_id}
```

**需要登录** ✅ — 仅该服务的创建者可操作

**逻辑**：软删除，设置 `is_deleted = true`，数据库仍保留记录

**成功响应**

```json
{
  "code": 0,
  "message": "success",
  "data": { "id": "uuid" }
}
```

**失败场景**

| code | message | 说明 |
|---|---|---|
| 403 | "Forbidden" | 不是该服务的创建者 |
| 404 | "Service not found" | 服务不存在 |

---

### 7. 上传服务者头像

上传一张照片作为服务者的展示头像。

```
POST /api/services/{service_id}/images/provider
```

**需要登录** ✅ — 仅该服务的创建者可操作

> ⚠️ 此接口使用 **form-data**

| 表单字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | file | ✅ | 单张图片 |

**成功响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "img-uuid",
    "path": "services/xxx/provider_xxx.jpg",
    "url": "https://xxx.supabase.co/services/xxx/provider_xxx.jpg"
  }
}
```

> 上传后自动替换旧头像。返回的 `url` 可直接用于 `<img>` 标签展示。
> 也可以直接用 `PUT /api/services/{id}` 传 `provider_image` 字段设置外部图片 URL。

**失败场景**

| code | message | 说明 |
|---|---|---|
| 403 | "Forbidden" | 不是该服务的创建者 |
| 404 | "Service not found" | 服务不存在 |

---

### 8. 上传资质佐证图

上传服务相关的资质、佐证图片。可多次调用，累加上传。

```
POST /api/services/{service_id}/images
```

**需要登录** ✅ — 仅该服务的创建者可操作

> ⚠️ 此接口使用 **form-data**

| 表单字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| files | file[] | ✅ | 可一次传多张，**每篇服务最多6张** |

**成功响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "images": [
      { "id": "img-uuid", "path": "services/xxx/yyy.jpg", "url": "https://xxx.supabase.co/..." },
      { "id": "img-uuid2", "path": "services/xxx/zzz.jpg", "url": "https://xxx.supabase.co/..." }
    ],
    "image_count": 2
  }
}
```

**失败场景**

| code | message | 说明 |
|---|---|---|
| 403 | "Forbidden" | 不是该服务的创建者 |
| 404 | "Service not found" | 服务不存在 |
| 400 | "Maximum 6 images per service" | 图片超过6张上限 |

---

### 9. 删除资质佐证图

```
DELETE /api/services/{service_id}/images/{image_id}
```

**需要登录** ✅ — 仅该服务的创建者可操作

**成功响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "images": [ /* 剩余的图片列表 */ ],
    "image_count": 0
  }
}
```

**失败场景**

| code | message | 说明 |
|---|---|---|
| 403 | "Forbidden" | 不是该服务的创建者 |
| 404 | "Service not found" | 服务不存在 |
| 404 | "Image not found" | 要删除的图片不存在 |

---

## 前端对接流程

### 发布流程

```
填写表单        ──→  上传头像（可选）     ──→  上传资质图（可选）  ──→  提交创建
(选分类/填信息)       POST .../images/provider    POST .../images         POST /services
                        拿到 url 回填             拿到 images 列表
```

简化方案：先 `POST /services` 创建服务拿到 id，再上传头像和资质图。

### 浏览流程

```
首页卡片 ──→ 服务列表页 ──→ 详情页（未登录看到内容，看不到联系方式）
GET /services         GET /services/{id}
                                          ↓ 登录后
                                  可看到联系方式
```

列表卡片展示 `provider_image` 作为服务者头像。

### 管理流程

```
我的服务列表 ──→ 编辑 / 管理图片 / 下架
GET /services/mine    PUT /services/{id}
                      POST/DELETE .../images/...
                      DELETE /services/{id}
```

---

## 安全提醒

以下文案前端在详情页**固定展示**（不需要后端返回）：

> ⚠️ 该服务者未经过平台认证，联系及交易时请格外注意人身和财产安全。DoxieLand 不承担任何责任。

当 `is_verified = true` 时可隐藏此提示或改为"已认证"标识。

---

## 分类标签颜色映射（前端用）

| category | 颜色 |
|---|---|
| walking | green |
| veterinary | red |
| boarding | blue |
| grooming | purple |
| lost_found | orange |
| meetup | pink |
| other | slate |

---

## 错误码速查

| code | message | 常见原因 |
|---|---|---|
| 400 | "Invalid category..." | category 传了不存在的值 |
| 400 | "Invalid fee_type..." | fee_type 传了不支持的值 |
| 400 | "At least one contact method is required" | phone 和 wechat 都为空 |
| 400 | "Maximum 6 images per service" | 资质图超过6张上限 |
| 400 | "No fields to update" | 更新时请求体为空 |
| 401 | "token invalid / token expired" | 未登录或 token 过期 |
| 403 | "Forbidden" | 不是服务的创建者 |
| 404 | "Service not found" | 服务不存在或已删除 |
| 404 | "Image not found" | 要删除的图片不存在 |
