"""
애플리케이션 로깅 설정.

gunicorn/uvicorn은 자기 로거(uvicorn.*)에만 핸들러를 붙이므로, 루트 로거에
핸들러가 없으면 `app.*`·`audit` 로거의 INFO 로그는 어디에도 출력되지 않는다
(Python의 lastResort 핸들러는 WARNING 이상만 stderr로 보냄). 그 결과 프로덕션
Railway 로그에 감사 로그(user.delete 등)가 한 건도 남지 않았다.

루트 로거에 stdout StreamHandler를 한 번만 붙여 모든 앱 로그가 플랫폼 로그로
수집되게 한다.
"""
import logging
import os
import sys

_HANDLER_NAME = "voj-stdout"


def setup_logging(level: str | None = None) -> None:
    """루트 로거에 stdout 핸들러를 (중복 없이) 추가한다."""
    root = logging.getLogger()

    # 워커 재시작·테스트 재임포트 시 핸들러가 쌓이지 않도록 이름으로 중복 검사
    if any(getattr(h, "name", None) == _HANDLER_NAME for h in root.handlers):
        return

    level_name = (level or os.environ.get("LOG_LEVEL") or "INFO").upper()
    root.setLevel(getattr(logging, level_name, logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.name = _HANDLER_NAME
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root.addHandler(handler)

    # 감사 로거는 레벨 설정과 무관하게 항상 INFO 이상을 남긴다
    logging.getLogger("audit").setLevel(logging.INFO)
