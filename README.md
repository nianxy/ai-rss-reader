# RSS Reader

基于 `FastAPI + SQLAlchemy + Alembic + APScheduler` 的 RSS 阅读器。

## 功能
- HTTP 服务
- 按 YAML 配置周期抓取 RSS
- 文章去重入库
- 调用 LLM 生成简短摘要和重点总结
- 每日按分类汇总并通过邮件发送
- 文章详情页和中转链接

## 快速开始
1. 安装依赖
   ```bash
   pip install -e .
   ```
2. 复制环境变量
   ```bash
   cp .env.example .env
   ```
3. 初始化数据库
   ```bash
   alembic upgrade head
   ```
4. 启动服务
   ```bash
   uvicorn app.main:app --reload
   ```

## 配置
- RSS 配置文件：`config/rss_config.yaml`
- 默认抓取与汇总任务会在服务启动时注册
