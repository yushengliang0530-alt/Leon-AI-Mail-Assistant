# Leon AI — 英文商务写作助手

面向中国职场人员、外贸人员和工程项目人员的 Streamlit 英文商务邮件助手。应用通过 DeepSeek API 生成或优化专业英文邮件，并提供动态签名、结构化输出、中文错误提示和可选测试访问码。

## 当前版本

**Beta 0.9 · 2026-07-29**

当前线上版本已部署至 Streamlit Community Cloud，仅面向受邀用户进行测试。测试版本提供英文邮件生成与优化功能，但尚未开放正式用户注册、支付、订阅和使用额度管理。请勿输入高度敏感信息，生成结果发送前请人工检查。

## 主要功能

- 根据中文需求生成英文商务邮件
- 优化已有英文邮件并保留事实、立场和核心意思
- 支持正式、友好、明确强硬、简洁和高管简洁等语气
- 自定义发件人姓名、职位、公司和联系方式
- 由 Python 本地逻辑生成签名
- 显示安全的 AI 服务状态、耗时和可用 token 用量
- 提供 8000 字符限制、重复请求保护和一次 JSON 修复重试
- 提供可选的小范围测试访问码

## 1. 本地运行

推荐使用 Python 3.12：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

然后访问 `http://127.0.0.1:8501`。

运行自动化测试：

```bash
python -m unittest discover -s tests -v
```

测试使用模拟 DeepSeek 客户端，不会产生真实 API 费用。

## 2. 本地 Secrets 配置

复制安全示例：

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

在本地 `.streamlit/secrets.toml` 中配置：

```toml
DEEPSEEK_API_KEY = "your-deepseek-api-key"
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
APP_ACCESS_CODE = "choose-a-test-access-code"
```

`APP_ACCESS_CODE` 可选。未配置时本地开发不受阻断，并显示“测试访问保护尚未启用”。不要将 `.streamlit/secrets.toml` 上传到 GitHub。

## 3. GitHub 上传前检查

执行：

```bash
git status --short
git check-ignore .streamlit/secrets.toml .env .venv
git ls-files .streamlit/secrets.toml .env
```

最后一条命令应没有输出。确认仓库中只包含 `.streamlit/secrets.toml.example`，不包含真实 Secrets、虚拟环境、缓存或测试覆盖率文件。

## 4. Streamlit Community Cloud 部署

1. 在 GitHub 创建空仓库并推送本项目。
2. 登录 Streamlit Community Cloud，选择 **Create app**。
3. 选择 GitHub 仓库和 `main` 分支。
4. 入口文件填写 `app.py`。
5. 在 **Advanced settings** 中选择 Python 3.12。
6. 配置云端 Secrets 后部署。

项目提供 `runtime.txt` 作为运行版本说明。Community Cloud 当前主要通过部署页面的 **Advanced settings** 选择 Python 版本；部署后如需更换 Python 版本，通常需要重新部署应用。

## 5. 云端 Secrets 配置

在 Community Cloud 的应用设置中打开 Secrets，将本地 Secrets 的 TOML 配置粘贴进去：

```toml
DEEPSEEK_API_KEY = "your-deepseek-api-key"
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
APP_ACCESS_CODE = "choose-a-test-access-code"
```

不要把真实 `secrets.toml` 提交到 GitHub。云端 Secrets 由 Streamlit 平台单独保存。

## 6. 测试访问码设置

- 配置 `APP_ACCESS_CODE` 后，首次访问会显示中文验证页。
- 正确输入后，当前 Streamlit session 会保持通过状态。
- 错误访问码不会进入主应用，也不会调用 DeepSeek。
- 访问码不会写入日志或业务代码。
- 这只是小范围外部测试门禁，不是正式身份认证，不适合保护高价值或高度敏感数据。

## 7. 部署后验证

部署完成后依次检查：

1. 未验证访问码时无法看到主应用。
2. 错误访问码被拒绝，正确访问码可以进入。
3. 页面显示“运行环境：云端部署”。
4. 生成和优化邮件各测试一次。
5. AI 服务状态能显示连接成功和请求耗时。
6. 邮件正文没有默认发件人姓名。
7. 日志中没有 API Key、访问码、用户邮件内容或完整异常堆栈。

## 8. 常见部署错误

### 缺少 DeepSeek API Key

检查 Community Cloud 的 Secrets 设置，不要将密钥写入代码。

### 模型不可用或余额不足

确认 `DEEPSEEK_MODEL` 仍是当前可用模型，并检查 DeepSeek 账户额度。

### 依赖安装失败

确认仓库根目录存在 `requirements.txt`，并在高级设置中选择 Python 3.12。

### 修改 Python 版本没有生效

Community Cloud 的 Python 版本在部署时选择。必要时记录应用配置后删除并重新部署。

### 修改 Secrets 后页面未更新

保存云端 Secrets，然后重启应用。

## 9. 更新应用的方法

完成本地修改和测试后：

```bash
git add .
git commit -m "describe your update"
git push
```

Community Cloud 会检测 GitHub 仓库的新提交并更新应用。推送前始终重新运行测试和 Secrets 跟踪检查。

## 安全与隐私

- 用户主动生成或优化邮件时，输入内容会发送至 DeepSeek API。
- 不要输入密码、身份证号、银行卡、商业秘密或其他高度敏感信息。
- AI 结果仅供参考，发送前应人工检查。
- 应用不会在打开页面时自动调用 API。
- 页面不会显示 API Key、访问码、系统路径、服务器 IP 或内部环境变量。
- `Leon AI` 仅是产品品牌，不会成为默认发件人姓名。
