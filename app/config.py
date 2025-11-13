import os
from typing import List


class Settings:
    def __init__(self) -> None:
        self.public_base_url: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
        self.bot_token: str = os.getenv("BOT_TOKEN", "")

        self.admin_owner_ids: List[int] = self._parse_admin_ids(
            os.getenv("ADMIN_OWNER_IDS", "")
        )

        self.bot_api_user: str | None = os.getenv("BOT_API_USER") or None
        self.bot_api_pass: str | None = os.getenv("BOT_API_PASS") or None

        self.wallet_master_key: str | None = os.getenv("WALLET_MASTER_KEY") or None
        self.faucet_amount: int = int(os.getenv("FAUCET_AMOUNT", "100"))
        self.faucet_token: str = os.getenv("FAUCET_TOKEN", "SLH")

        self.port: int = int(os.getenv("PORT", "8080"))

    @staticmethod
    def _parse_admin_ids(value: str) -> List[int]:
        if not value:
            return []
        ids: List[int] = []
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                ids.append(int(part))
            except ValueError:
                continue
        return ids


settings = Settings()
