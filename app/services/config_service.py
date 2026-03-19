from pathlib import Path

import yaml

from app.schemas.config_schema import RSSConfig


def load_rss_config(config_path: str) -> RSSConfig:
    raw = yaml.safe_load(Path(config_path).read_text(encoding='utf-8'))
    return RSSConfig.model_validate(raw)
