# 快速开始

## 注册与激活
1. 访问官网，点击「免费注册」
2. 验证邮箱
3. 创建第一个项目，获取 API 密钥

## 第一个 API 调用
```bash
curl -X POST https://api.example.com/v1/analyze \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

## SDK 支持
- Python：`pip install example-sdk`
- Node.js：`npm install @example/sdk`
- Java、Go、Ruby：社区维护，见 GitHub

## 新手常见问题
- API 密钥在控制台「设置」→「API 密钥」中生成
- 免费版密钥有效期 1 年，Pro/Enterprise 永久有效
- 同一账号最多创建 5 个 API 密钥（免费版限 1 个）
