"""Shared message formatter for channel integrations.

Re-exports from app.bots.formatter for backward compatibility,
and provides the unified format_text_results from notifier.
"""

from app.bots.formatter import (  # noqa: F401
    format_list_summary as format_list_text,
    format_slack_blocks as _format_slack_blocks,
    format_slack_list_blocks,
    format_telegram_html as format_markdown,
    format_telegram_list_html as format_list_markdown,
    format_text_results as format_text,
)

from app.channels.notifier import format_text_results  # noqa: F401
