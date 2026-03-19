# AGENT.md

## 项目当前状态
- 项目已从 `requirements.md` 落地为可运行实现：`FastAPI + SQLAlchemy + Alembic + APScheduler`。
- 已实现能力：
  - HTTP 服务与健康检查：`/healthz`
  - 文章查询与详情页：`/articles/{id}`、`/go/{id}`
  - YAML 配置加载 RSS 分类与源
  - 定时抓取 RSS、按去重键入库、同文多来源别名合并
  - LLM 文章摘要（短摘要 + 重点总结）
  - 前一日分类汇总、LLM 去重、HTML 邮件发送
  - Alembic migration 管理数据库结构

## 环境与依赖
- 已创建 conda 环境：`rss-reader`
- Miniconda 路径：`/home/nianxingyan/miniconda3/bin/conda`
- 依赖已安装完成（editable install）

## 已完成验证
- `alembic upgrade head` 成功
- 抓取脚本成功写入数据：`category=tech inserted=20`
- DB 计数校验：`20` 条
- 服务启动与健康检查通过：`GET /healthz -> {"ok": true}`

## 常用命令
- 激活环境：
  - `source /home/nianxingyan/miniconda3/etc/profile.d/conda.sh`
  - `conda activate rss-reader`
- 安装依赖：
  - `python -m pip install -e .`
- 迁移数据库：
  - `alembic upgrade head`
- 启动服务：
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- 手动执行抓取：
  - `python scripts/run_fetch_once.py`
- 手动执行日报：
  - `python scripts/run_daily_digest_once.py`

## 关键文件
- 应用入口：`app/main.py`
- 路由：`app/api/routes.py`
- 抓取服务：`app/services/rss_service.py`
- 汇总服务：`app/services/digest_service.py`
- 定时任务：`app/services/scheduler_service.py`
- LLM 服务：`app/services/llm_service.py`
- 数据模型：`app/models/article.py`
- 迁移脚本：`alembic/versions/20260319_0001_init.py`
- RSS 配置：`config/rss_config.yaml`
- 模板：`app/templates/daily_digest.html`、`app/templates/article_detail.html`

## 配置说明
- 环境变量模板：`.env.example`
- 当前若未配置 `LLM_API_KEY`，系统会使用本地降级摘要逻辑（非真实 LLM 输出）。
- 当前若未配置 SMTP 信息，邮件发送会跳过。

## 已知行为
- 日报按“前一天”数据汇总，因此当天新抓取数据不会出现在 `run_daily_digest_once.py` 结果中（输出 `categories=0` 属正常）。

## 后续建议
1. 增加测试（抓取、去重、汇总、路由）。
2. 为 LLM 返回增加更稳健的 JSON 解析与重试。
3. 为抓取/摘要/邮件增加日志与监控指标。
4. 增加 Dockerfile 与 docker-compose 便于部署。
