import re


def markdown_to_slack(text: str) -> str:
    """
    Convert markdown text to Slack's mrkdwn format.
    
    Slack mrkdwn differences from standard markdown:
    - Bold: **text** -> *text*
    - Italic: *text* or _text_ -> _text_
    - Strikethrough: ~~text~~ -> ~text~
    - Code blocks: ```lang\ncode``` -> ```code```
    - Links: [text](url) -> <url|text>
    - Headers: # text -> *text*
    - Lists: preserved as-is
    """
    if not text:
        return text
    
    # Preserve code blocks
    code_blocks = []
    def preserve_code_block(match):
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"
    
    # Preserve inline code
    inline_codes = []
    def preserve_inline_code(match):
        inline_codes.append(match.group(0))
        return f"__INLINE_CODE_{len(inline_codes)-1}__"
    
    # Store code blocks and inline code
    text = re.sub(r'```[\s\S]*?```', preserve_code_block, text)
    text = re.sub(r'`[^`]+`', preserve_inline_code, text)
    
    # Convert headers (h1-h6) to bold
    text = re.sub(r'^#{1,6}\s+(.+)$', r'*\1*', text, flags=re.MULTILINE)
    
    # Convert bold syntax: **text** -> *text*
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    
    # Convert italic syntax: _text_ stays as is, *text* -> _text_
    # First, temporarily replace _text_ with placeholder
    text = re.sub(r'_([^_]+)_', r'__ITALIC__\1__ITALIC__', text)
    # Convert *text* to _text_
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)', r'_\1_', text)
    # Restore _text_
    text = text.replace('__ITALIC__', '_')
    
    # Convert strikethrough: ~~text~~ -> ~text~
    text = re.sub(r'~~([^~]+)~~', r'~\1~', text)
    
    # Convert links: [text](url) -> <url|text>
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', text)
    
    # Convert blockquotes: > text -> > text (Slack uses same format)
    # No conversion needed
    
    # Restore code blocks (remove language identifier)
    for i, code_block in enumerate(code_blocks):
        # Remove language identifier from code blocks
        cleaned_block = re.sub(r'```\w*\n', '```\n', code_block)
        text = text.replace(f"__CODE_BLOCK_{i}__", cleaned_block)
    
    # Restore inline code
    for i, inline_code in enumerate(inline_codes):
        text = text.replace(f"__INLINE_CODE_{i}__", inline_code)
    
    return text