# 🔐 安全最佳实践指南

本文档说明如何安全地管理AI助教RAG系统的API密钥和敏感信息。

## 🚨 安全风险警告

### ❌ 错误做法（会导致密钥泄露）
1. **硬编码API密钥**: 在代码中直接写入真实的API密钥
2. **提交密钥到Git**: 将包含真实密钥的文件提交到版本控制系统
3. **使用默认值**: 使用示例代码中的"dummy"或"placeholder"值
4. **公开分享配置**: 在论坛、社交媒体等地方分享配置文件

### ✅ 正确做法
1. **使用环境变量**: 所有敏感信息通过环境变量加载
2. **Git忽略规则**: 确保`.env`等敏感文件被`.gitignore`排除
3. **分离配置**: 使用模板文件，实际配置文件本地保存
4. **定期轮换**: 定期更换API密钥

## 🛡️ 安全配置步骤

### 1. 环境变量配置

#### 方法一：使用.env文件（推荐）
```bash
# 复制模板文件
cp .env.example .env

# 编辑.env文件，设置真实API密钥
nano .env  # 或使用其他编辑器
```

#### 方法二：直接设置环境变量
```bash
# 在终端中设置
export SILICONFLOW_API_KEY='your-actual-api-key'
export OPENAI_LIKE_API_KEY='your-actual-openai-like-key'

# 或在启动脚本中设置
SILICONFLOW_API_KEY='your-key' python web_app.py
```

### 2. Git安全配置

检查`.gitignore`文件包含以下条目：
```
# 环境变量文件
.env
.env.local
.env.production
.env.development

# 配置文件
config.local.py
local_config.py
secrets.*

# 其他敏感文件
*.key
*.pem
*.p12
```

### 3. 生产环境安全

#### 使用Docker环境变量
```dockerfile
# Dockerfile
ENV SILICONFLOW_API_KEY=""
ENV OPENAI_LIKE_API_KEY=""

# 运行时传入
docker run -e SILICONFLOW_API_KEY="your-key" your-app
```

#### 使用云服务密钥管理
- **AWS**: AWS Secrets Manager / Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Secret Manager
- **阿里云**: KMS 密钥管理服务

## 🔍 安全检查清单

在提交代码前，确认以下检查项：

- [ ] `.env`文件在`.gitignore`中
- [ ] 代码中没有硬编码的API密钥
- [ ] 配置文件中只有环境变量引用
- [ ] 示例密钥已替换为占位符
- [ ] 敏感日志信息已移除
- [ ] 临时文件不包含密钥

## 🚨 密钥泄露应急处理

如果怀疑API密钥已泄露：

1. **立即禁用**: 登录API提供商控制台，禁用泄露的密钥
2. **生成新密钥**: 创建新的API密钥
3. **更新配置**: 更新所有使用该密钥的配置
4. **检查日志**: 检查是否有异常访问
5. **通知团队**: 通知可能受影响的团队成员

## 🛠️ 开发环境安全

### VS Code配置
在`.vscode/settings.json`中添加：
```json
{
    "secrets.ignore": [
        "**/.env",
        "**/config.local.py"
    ]
}
```

### Git Hooks（可选）
创建pre-commit hook检查密钥泄露：
```bash
#!/bin/sh
# .git/hooks/pre-commit
if git diff --cached --name-only | xargs grep -l "sk-\|AIza\|your-.*-key" 2>/dev/null; then
    echo "❌ 检测到可能的API密钥泄露！"
    echo "请移除代码中的硬编码密钥后再提交。"
    exit 1
fi
```

## 📚 参考资源

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Git忽略文件最佳实践](https://git-scm.com/docs/gitignore)
- [Docker安全最佳实践](https://docs.docker.com/develop/dev-best-practices/)

## 🆘 常见问题

**Q: 我不小心提交了API密钥怎么办？**
A: 立即使用`git filter-branch`或`git-filter-repo`从历史记录中移除，然后在API提供商处重新生成密钥。

**Q: 如何在团队中安全共享配置？**
A: 使用环境特定的配置文件模板，通过安全渠道分享实际的密钥值。

**Q: 生产环境如何管理密钥？**
A: 使用云服务商的密钥管理服务，或Kubernetes Secrets等容器编排工具的密钥管理功能。