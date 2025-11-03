# IP查询API服务

基于Flask和httpx的IP地址威胁情报查询API服务，集成百度云IP威胁情报API，支持代理、自动User-Agent和并发查询

> **项目描述**: 本项目通过百度云IP威胁情报API查询IP地址的安全状态、威胁类型、ISP信息、地理位置等详细数据，支持单个查询和批量并发查询，提供RESTful API接口和自动生成的Swagger文档。

## 功能特性

- ✅ 支持GET请求查询IP地址威胁情报
- ✅ 使用httpx进行HTTP请求（支持HTTP/HTTPS代理）
- ✅ 自动生成fake User-Agent进行请求
- ✅ 支持多进程/多线程并发批量查询
- ✅ 支持线程池批量查询（推荐用于I/O密集型）
- ✅ 支持进程池批量查询（适用于计算密集型）
- ✅ JSON格式统一返回数据
- ✅ 内置IP地址格式验证
- ✅ 健康检查接口
- ✅ 自动生成Swagger/OpenAPI文档
- ✅ 交互式API文档（在线测试）
- ✅ 集成百度云IP威胁情报API

## 安装依赖

```bash
pip install -r requirements.txt
```

**核心依赖**:
- Flask: Web框架
- httpx: HTTP客户端（核心功能）
- fake-useragent: 生成随机User-Agent
- flask-restx: 自动生成API文档
- DrissionPage: 页面操作库（当前版本未使用，可能用于后续功能）

> **注意**: 如果不需要DrissionPage，可从requirements.txt中移除

## 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

**🎯 访问地址**:
- 📖 首页指南: http://localhost:5000/
- 📘 Swagger文档: http://localhost:5000/api/
- 🧪 在线测试: 在Swagger文档页面直接测试API
- 📤 导出文档: http://localhost:5000/api/api-docs

## API接口文档

### 1. IP查询接口（httpx，集成百度云API）

**请求方式**: GET

**请求地址**: `/api/query`

**请求参数**:
- `ip` (必需): 要查询的IP地址
- `method` (可选): HTTP请求方法，GET或POST（默认为GET）
- `format` (可选): 返回格式，支持 `text` 或 `json`，默认为 `text`

> **注意**: 当前版本代理地址已在代码中硬编码为：`15951531090:1Dkvavbt@tunnel-42.91http.cc:10630`

**请求示例**:
```bash
# JSON格式返回（推荐）
curl "http://localhost:5000/api/query?ip=8.8.8.8&format=json"

# 纯文本格式返回
curl "http://localhost:5000/api/query?ip=8.8.8.8&format=text"
```

**返回示例**:

**纯文本格式**:
```
IP: 8.8.8.8
Status: success
Method: httpx
```

**JSON格式**:
```json
{
  "ip": "8.8.8.8",
  "status": "success",
  "data": {
    "overall": {
      "score": 0,
      "risk_level": "low",
      "threat_types": [],
      "tags": []
    },
    "ip_base": {
      "isp": "Google LLC",
      "location": "United States",
      "asn": "AS15169",
      "is_proxy": false,
      "is_tor": false
    }
  }
}
```

> **注意**: 返回数据格式取决于百度云API的实际响应结构

### 2. 批量并发查询接口

**请求方式**: POST

**请求地址**: `/api/batch-query`

**请求体** (JSON):
```json
{
  "ips": ["8.8.8.8", "1.1.1.1"],
  "proxy": "http://proxy.example.com:8080",
  "mode": "thread"
}
```

**请求参数**:
- `ips` (必需): IP地址数组
- `proxy` (可选): 代理服务器地址
- `mode` (可选): 并发模式，支持 `thread`（线程池）或 `process`（进程池），默认为 `thread`

**请求示例**:
```bash
curl -X POST http://localhost:5000/api/batch-query \
  -H "Content-Type: application/json" \
  -d '{"ips": ["8.8.8.8", "1.1.1.1"], "mode": "thread"}'
```

**返回示例**:
```json
{
  "status": "success",
  "total": 2,
  "mode": "thread",
  "results": [
    {
      "ip": "8.8.8.8",
      "status": "success",
      "data": {
        "overall": {...},
        "ip_base": {...}
      }
    },
    {
      "ip": "1.1.1.1",
      "status": "success",
      "data": {
        "overall": {...},
        "ip_base": {...}
      }
    }
  ]
}
```

> **说明**: 批量查询使用线程池/进程池并发执行，默认代理地址同样生效

### 3. 健康检查接口

**请求方式**: GET

**请求地址**: `/api/health`

**响应示例**:
```json
{
  "status": "healthy",
  "service": "IP Query API"
}
```

## 代码结构

```
IpCheckApi/
├── app.py              # Flask API应用主文件（集成Flask-RESTX自动文档）
├── query_ip.py         # IP查询服务模块（集成百度云API）
├── requirements.txt    # 依赖文件
├── API_DOCS.md         # API文档使用说明
└── README.md          # 项目说明文档
```

### 文件说明

- **app.py**: Flask主应用，集成Flask-RESTX自动生成Swagger文档，提供REST API接口
- **query_ip.py**: 核心查询模块，包含IPQueryService类和并发查询函数
- **API_DOCS.md**: API文档使用说明（如果存在）

## 自动文档生成

### Swagger/OpenAPI文档

直接在 `app.py` 中集成了Flask-RESTX，自动生成完整的API文档：

#### 🎯 主要特性

1. **交互式文档页面**
   - 访问 http://localhost:5000/api/ 查看Swagger UI
   - 在线测试所有API接口
   - 自动生成请求示例

2. **OpenAPI 3.0规范**
   - 标准化的API文档格式
   - 支持JSON/YAML导出
   - 兼容各种API客户端工具

3. **自动文档特性**
   - 自动解析函数docstring生成描述
   - 自动验证请求参数
   - 自动生成响应模型
   - 自动生成错误响应说明

#### 📖 文档页面说明

- **首页指南** (http://localhost:5000/)
  - 快速使用指南
  - 功能特性说明
  - API接口列表
  - curl命令示例

- **Swagger UI** (http://localhost:5000/api/)
  - 交互式API文档
  - 在线测试功能
  - 请求/响应示例
  - 错误代码说明

#### 💡 使用建议

**开发阶段**: 使用 `app.py` 获得最佳开发体验，文档会自动生成
**生产阶段**: 可在Flask配置中禁用文档功能（设置 `doc=False`）

## 核心类说明

### IPQueryService（位于query_ip.py）
IP查询服务类，负责：
- 使用httpx进行HTTP请求（集成百度云IP威胁情报API）
- 内置代理配置（`15951531090:1Dkvavbt@tunnel-42.91http.cc:10630`）
- 自动生成fake User-Agent进行请求
- 格式化返回数据（返回overall和ip_base两个数据段）
- 提供线程池批量查询功能
- 支持并发数配置（默认CPU核心数+4，最大不超过32）

### 核心方法
- `query_ip_with_httpx(ip_address, proxy_url=None, method="GET")`: 单个IP查询
- `batch_query(ip_list, proxy_url=None, max_workers=None)`: 线程池批量查询
- `close()`: 关闭线程池

### 独立函数
- `batch_query_multiprocess()`: 进程池批量查询（跨进程并发）
- `_query_ip_multiprocess()`: 多进程查询辅助函数

### API路由（app.py）
- `GET /api/query`: IP查询接口（集成百度云API）
- `POST /api/batch-query`: 批量并发查询接口（支持多进程/多线程）
- `GET /api/health`: 健康检查接口

### 数据结构
查询返回的data字段包含两个主要部分：
- `overall`: IP威胁情报整体评分和风险信息
- `ip_base`: IP基础信息（ISP、地理位置、ASN等）

## 自定义配置

### 修改默认代理地址
在 `query_ip.py` 的 `query_ip_with_httpx` 方法中修改硬编码的代理地址（第115行和第203行）：
```python
# app.py第115行
result = query_service.query_ip_with_httpx(
    ip_address, "your-proxy:port"  # 修改这里
)

# query_ip.py第203行（测试代码）
httpx_res = query_service.query_ip_with_httpx(
    ip, "your-proxy:port"  # 修改这里
)
```

### 修改代理格式
在 `query_ip.py` 的 `query_ip_with_httpx` 方法中修改代理格式（第55-56行）：
```python
if proxy_url and not proxy_url.startswith("http"):
    proxy_url = "http://" + proxy_url

# 或者直接使用完整格式
proxy_url = "http://username:password@proxy-server:port"
```

### 调整并发配置
在 `query_ip.py` 的 `IPQueryService.__init__` 方法中修改并发数（第33行）：
```python
# 默认计算方式
self.max_workers = max_workers or min(32, (multiprocessing.cpu_count() or 1) + 4)

# 修改为固定值
self.max_workers = max_workers or 8  # 固定为8个并发
```

### 修改请求头
在 `query_ip.py` 的 `query_ip_with_httpx` 方法中修改请求头（第63-71行）：
```python
headers = {
    "User-Agent": user_agent,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    # 添加自定义请求头
    "X-Custom-Header": "your-value",
    "Authorization": "Bearer your-token",
}
```

### 修改API基础地址
在 `query_ip.py` 的 `IPQueryService.__init__` 方法中修改API基础地址（第28-30行）：
```python
self.base_url = "https://your-custom-api.com/ip"
self.overall_baseurl = f"{self.base_url}/threat"
self.ip_base_baseurl = f"{self.base_url}/info"
```

## 错误处理

- 400: 缺少必需参数或IP地址格式无效
- 500: 服务器内部错误

## 并发查询性能示例

### 线程池模式（推荐）
```python
from query_ip import query_service

# 批量查询多个IP（使用默认代理）
ip_list = ["8.8.8.8", "1.1.1.1", "114.114.114.114", "223.5.5.5"]
results = query_service.batch_query(ip_list, max_workers=8)

for result in results:
    print(f"IP: {result['ip']}, Status: {result['status']}")
    if result['status'] == 'success':
        print(f"  Overall Risk: {result['data']['overall']}")
        print(f"  ISP: {result['data']['ip_base']}")
```

### 进程池模式
```python
from query_ip import batch_query_multiprocess

# 使用多进程查询（适用于计算密集型任务）
ip_list = ["8.8.8.8", "1.1.1.1"]
results = batch_query_multiprocess(ip_list, max_workers=4)

for result in results:
    print(f"IP: {result['ip']}, Status: {result['status']}")
```

### 直接单次查询
```python
from query_ip import query_service

# 查询单个IP
result = query_service.query_ip_with_httpx("8.8.8.8")
print(f"IP: {result['ip']}")
print(f"Overall: {result['data']['overall']}")
print(f"Base Info: {result['data']['ip_base']}")
```

## 注意事项

1. **代理配置**: 当前版本代理地址为硬编码，如需更换请修改 `app.py` 第115行和 `query_ip.py` 第203行
2. **API依赖**: 本服务依赖百度云IP威胁情报API，需确保代理可正常访问 `cloud.baidu.com`
3. **生产部署**: 生产环境中请关闭Flask的debug模式，设置 `debug=False`
4. **频率限制**: 建议添加请求频率限制，避免触发API限流
5. **代理可用性**: 代理服务器需要可正常访问百度云API才能使用
6. **错误处理**: httpx会自动处理HTTP状态码和错误，返回错误信息在`error`字段中
7. **User-Agent**: 使用fake-useragent随机生成真实浏览器User-Agent字符串，提高请求成功率
8. **并发选择**:
   - 线程池（thread）适用于I/O密集型任务，CPU开销较小，推荐使用
   - 进程池（process）适用于计算密集型任务，但内存开销更大
9. **并发数建议**: 合理设置并发数避免过载（建议不超过32个并发）
10. **资源清理**: 程序退出前会自动关闭线程池，确保资源正确释放
11. **数据格式**: 返回数据包含`overall`（威胁情报）和`ip_base`（基础信息）两个主要字段
12. **多进程限制**: 在Windows上多进程模式需要使用`if __name__ == "__main__"`保护
13. **超时设置**: httpx请求超时设置为20秒，可根据需要调整
14. **API Key**: 如百度云API需要认证，请自行在请求头中添加认证信息