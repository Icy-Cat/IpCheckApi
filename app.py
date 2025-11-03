"""
带自动文档生成的Flask API应用

使用Flask-RESTX自动生成Swagger/OpenAPI文档
访问根路径 / 查看文档指南
"""

from flask import Flask, request, jsonify, render_template_string
import re
import json
import os
from dotenv import load_dotenv
from flask_restx import Api, Resource, fields, Namespace
from query_ip import query_service, batch_query_multiprocess

load_dotenv()

proxy_url = os.getenv("PROXY_URL")

app = Flask(__name__)
app.config["RESTX_MASK_SWAGGER"] = False
app.config["JSON_AS_ASCII"] = False  # 确保JSON响应正确显示中文
app.config["RESTX_JSON"] = {"ensure_ascii": False}  # Flask-RESTX的JSON配置
app.config["JSONIFY_MIMETYPE"] = "application/json; charset=utf-8"

# 创建API实例
api = Api(
    app,
    version="1.0",
    title="IP查询API",
    description="自动生成API文档的IP地址查询服务",
    doc="/",  # 文档访问路径
    prefix="/api",
    # contact="API支持团队",
    # contact_email="support@example.com",
)

# 创建命名空间
ns = Namespace("ip", description="IP地址查询相关接口")
api.add_namespace(ns)

# 定义数据模型
ip_model = api.model(
    "IP地址查询响应",
    {
        "ip": fields.String(required=True, description="查询的IP地址"),
        "status": fields.String(description="查询状态", example="success"),
        "cached_at": fields.String(description="缓存写入时间（UTC+8 ISO8601）"),
        "data": fields.Raw(description="查询结果数据"),
    },
)

batch_query_model = api.model(
    "批量查询请求",
    {
        "ips": fields.List(fields.String, required=True, description="IP地址列表"),
        "mode": fields.String(description="并发模式", enum=["thread", "process"], default="thread"),
    },
)

batch_query_response_model = api.model(
    "批量查询响应",
    {
        "status": fields.String(description="状态"),
        "total": fields.Integer(description="总数量"),
        "mode": fields.String(description="查询模式"),
        "results": fields.List(fields.Raw, description="查询结果列表"),
    },
)

error_model = api.model(
    "错误响应", {"status": fields.String(example="error"), "message": fields.String(description="错误信息")}
)


@ns.route("/query")
class IPQueryHttpx(Resource):
    @ns.doc("query_ip", description="使用httpx进行IP查询")
    @ns.expect(
        api.parser()
        .add_argument("ip", type=str, required=True, help="IP地址")
        .add_argument(
            "method", type=str, required=False, help="HTTP方法", choices=["GET", "POST"], default="GET"
        )
        .add_argument(
            "format", type=str, required=False, help="返回格式", choices=["text", "json"], default="text"
        )
    )
    @ns.marshal_with(ip_model, skip_none=True)
    @ns.response(400, "参数错误", error_model)
    @ns.response(500, "服务器错误", error_model)
    def get(self):
        """
        IP查询接口

        使用httpx进行HTTP请求，支持fake User-Agent
        """
        # 获取请求参数
        ip_address = request.args.get("ip")
        method = request.args.get("method", "GET").upper()
        format_type = request.args.get("format", "text").lower()

        # 验证IP地址
        if not ip_address:
            api.abort(400, "缺少必需参数：ip")

        # IP格式验证
        ip_pattern = re.compile(
            r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}"
            r"([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
        )
        if not ip_pattern.match(ip_address):
            api.abort(400, "无效的IP地址格式")

        # 验证请求方法
        if method not in ["GET", "POST"]:
            api.abort(400, "不支持的HTTP方法，只支持GET和POST")

        # 执行查询
        result = query_service.query_ip_with_cache(ip_address, proxy_url)

        # 如果是纯文本格式，返回字符串
        if format_type == "text":
            if result["status"] == "success":
                return result, 200, {"Content-Type": "text/plain"}
            else:
                return result, 500, {"Content-Type": "text/plain"}

        return result


@ns.route("/batch-query")
class BatchQuery(Resource):
    @ns.doc("batch_query", description="批量并发查询多个IP地址，支持多进程/多线程")
    @ns.expect(batch_query_model)
    @ns.marshal_with(batch_query_response_model)
    @ns.response(400, "参数错误", error_model)
    @ns.response(500, "服务器错误", error_model)
    def post(self):
        """
        批量并发查询接口

        支持多进程/多线程并发查询多个IP地址
        """
        try:
            # 解析请求体
            data = request.get_json()
            if not data or "ips" not in data:
                api.abort(400, "缺少必需参数：ips")

            ip_list = data.get("ips", [])
            # proxy_url = data.get("proxy")
            mode = data.get("mode", "thread")

            if not isinstance(ip_list, list) or len(ip_list) == 0:
                api.abort(400, "ips参数必须是IP地址数组且不能为空")

            # 验证所有IP地址
            ip_pattern = re.compile(
                r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}"
                r"([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
            )
            for ip in ip_list:
                if not ip_pattern.match(ip):
                    api.abort(400, f"无效的IP地址格式：{ip}")

            # 根据模式选择查询方式
            if mode == "process":
                results = batch_query_multiprocess(ip_list, proxy_url)
            else:
                results = query_service.batch_query(ip_list, proxy_url)

            return {"status": "success", "total": len(ip_list), "mode": mode, "results": results}

        except Exception as e:
            api.abort(500, str(e))


@ns.route("/health")
class HealthCheck(Resource):
    @ns.doc("health_check", description="检查API服务是否正常运行")
    @ns.response(200, "成功")
    def get(self):
        """
        健康检查接口
        """
        return {"status": "healthy", "service": "IP Query API"}


if __name__ == "__main__":

    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        query_service.close()
