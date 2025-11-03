from query_ip import query_service

ip = "36.184.64.231"
result1 = query_service.query_ip_with_cache(ip)
result2 = query_service.query_ip_with_cache(ip)

print("第一次查询:", result1)
print("第二次查询:", result2)
