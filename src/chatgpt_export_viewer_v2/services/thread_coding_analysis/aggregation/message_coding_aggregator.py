from __future__ import annotations

from ..detectors.command_pattern_detector import is_command_like_line
from ..detectors.prose_density_detector import is_prose_like_line
from ..detectors.stacktrace_pattern_detector import is_stacktrace_line
from ..detectors.symbol_density_detector import is_symbol_dense_code_line
from ..detectors.syntax_shape_detector import is_syntax_code_line
from ..segmentation.indented_block_segmenter import is_indented_code_line, split_lines
from ..segmentation.inline_backtick_segmenter import extract_inline_code_spans
from ..segmentation.markdown_fence_segmenter import extract_fenced_blocks
from ..thread_coding_models import ThreadCodingSignals
from ..thread_coding_policy import ThreadCodingPolicy


def analyze_message_text(text: str, signals: ThreadCodingSignals, policy: ThreadCodingPolicy) -> None:
    if not text:
        return

    fenced_blocks, remaining_after_fence = extract_fenced_blocks(text)
    for block in fenced_blocks:
        block_chars = len(block.strip())
        if block_chars <= 0:
            continue
        signals.fenced_blocks += 1
        signals.code_chars += block_chars

    inline_spans, remaining = extract_inline_code_spans(remaining_after_fence)
    for span in inline_spans:
        span_chars = len(span.strip())
        if span_chars <= 0:
            continue
        signals.inline_code_spans += 1
        signals.code_chars += span_chars

    for raw_line in split_lines(remaining):
        line = raw_line.rstrip()
        trimmed = line.strip()
        if not trimmed:
            continue

        line_chars = len(trimmed)

        if is_stacktrace_line(trimmed):
            signals.stacktrace_lines += 1
            signals.code_chars += line_chars
            continue

        if is_indented_code_line(line):
            signals.indented_code_lines += 1
            signals.code_chars += line_chars
            continue

        if is_command_like_line(trimmed):
            signals.command_lines += 1
            signals.code_chars += line_chars
            continue

        if is_syntax_code_line(trimmed) or is_symbol_dense_code_line(
            trimmed,
            minimum_density=policy.min_symbol_density,
        ):
            signals.syntax_code_lines += 1
            signals.code_chars += line_chars
            continue

        if is_prose_like_line(trimmed):
            signals.prose_lines += 1

        signals.non_code_chars += line_chars
