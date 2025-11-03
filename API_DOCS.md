# IP查询API - 自动文档生成版

## 🎯 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务（带自动文档）

```bash
python app_with_docs.py
```

### 3. 访问文档

- **首页**: http://localhost:5000/
- **Swagger交互式文档**: http://localhost:5000/api/

## 📖 文档特性

### ✅ 自动生成的Swagger文档包含：

1. **完整的API接口说明**
   - 每个接口的功能描述
   - 请求参数说明
   - 响应格式说明
   - 错误代码说明

2. **交互式在线测试**
   - 直接在文档页面测试API
   - 自动生成请求示例
   - 实时查看响应结果

3. **OpenAPI 3.0规范**
   - 标准的API文档格式
   - 支持导出为JSON/YAML
   - 兼容各种API客户端

## 🔍 API接口列表

### 1. IP查询（DrissionPage）
- **URL**: `GET /api/query`
- **功能**: 使用DrissionPage查询IP地址信息
- **参数**:
  - `ip`: IP地址（必需）
  - `format`: 返回格式（text/json，可选）

### 2. IP查询（httpx）
- **URL**: `GET /api/query/httpx`
- **功能**: 使用httpx查询IP地址信息
- **参数**:
  - `ip`: IP地址（必需）
  - `proxy`: 代理地址（可选）
  - `method`: GET/POST（可选）
  - `format`: 返回格式（可选）

### 3. 批量查询
- **URL**: `POST /api/batch-query`
- **功能**: 批量并发查询多个IP地址
- **请求体**:
```json
{
  "ips": ["8.8.8.8", "1.1.1.1"],
  "proxy": "http://proxy.example.com:8080",
  "mode": "thread"
}
```

### 4. 健康检查
- **URL**: `GET /api/health`
- **功能**: 检查API服务状态

## 📊 使用示例

### curl命令示例

```bash
# 单IP查询
curl "http://localhost:5000/api/query/httpx?ip=8.8.8.8&format=json"

# 批量查询
curl -X POST http://localhost:5000/api/batch-query \
  -H "Content-Type: application/json" \
  -d '{"ips": ["8.8.8.8", "1.1.1.1"], "mode": "thread"}'

# 健康检查
curl http://localhost:5000/api/health
```

### Python客户端示例

```python
import requests

# 查询单个IP
response = requests.get(
    "http://localhost:5000/api/query/httpx",
    params={"ip": "8.8.8.8", "format": "json"}
)
print(response.json())

# 批量查询
response = requests.post(
    "http://localhost:5000/api/batch-query",
    json={
        "ips": ["8.8.8.8", "1.1.1.1"],
        "mode": "thread"
    }
)
print(response.json())
```

## 🎨 Swagger UI功能

### 在线测试API
1. 打开 http://localhost:5000/api/
2. 点击要测试的接口
3. 点击 "Try it out"
4. 填写参数
5. 点击 "Execute"
6. 查看响应结果

### 导出API文档
- **JSON格式**: http://localhost:5000/api/api-docs
- **YAML格式**: http://localhost:5000/api/api-docs.yaml

### 客户端生成
使用swagger-codegen或其他工具可以基于文档生成各种语言的客户端：

```bash
# 生成Python客户端
swagger-codegen generate -i http://localhost:5000/api/api-docs -l python -o ./python-client
```

## ⚙️ 高级配置

### 自定义Swagger UI
```python
api = Api(
    app,
    doc='/api/',
    title='我的API',
    description='自定义描述',
    version='1.0.0',
    contact='support@example.com',
    # 更多配置...
)
```

### 禁用某些文档功能
```python
app.config['RESTX_MASK_SWAGGER'] = False
```

## 🔧 与原版对比

| 特性 | app.py | app_with_docs.py |
|------|--------|------------------|
| 基础API功能 | ✅ | ✅ |
| 自动文档生成 | ❌ | ✅ |
| Swagger UI | ❌ | ✅ |
| 在线测试 | ❌ | ✅ |
| OpenAPI规范 | ❌ | ✅ |
| 首页指南 | ❌ | ✅ |

## 📝 注意事项

1. **依赖**: 需要安装 `flask-restx`
2. **端口**: 默认监听5000端口
3. **文档**: 文档路径为 `/api/`
4. **兼容性**: 与原版API完全兼容
5. **性能**: 文档生成对性能影响极小

## 🚀 生产部署建议

1. **关闭debug模式**
```python
app.run(host="0.0.0.0", port=5000, debug=False)
```

2. **使用WSGI服务器**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app_with_docs:app
```

3. **隐藏Swagger文档**（生产环境）
```python
api = Api(app, doc='/api/', doc=False)  # 禁用文档
```

## 💡 小贴士

1. **访问首页** http://localhost:5000/ 查看快速指南
2. **Swagger文档** http://localhost:5000/api/ 支持在线测试
3. **直接使用** `/api/` 前缀的所有接口
4. **导出文档** 为JSON/YAML格式以便离线查看

---

**享受自动生成的API文档吧！** 🎉
