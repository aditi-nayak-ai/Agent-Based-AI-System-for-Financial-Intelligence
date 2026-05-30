def sanitize_input(text: str) -> str:
    """
    Strip characters commonly used in SQL injection and prompt injection
    before the query reaches any agent or database layer.
 
    This is a lightweight first-pass filter, not a substitute for
    parameterised queries in the DB layer. Keep both defences in place.
    """
    # SQL injection basics
    text = text.replace(";", "")
    text = text.replace("--", "")
    text = text.replace("/*", "")
    text = text.replace("*/", "")
 
    # Prompt injection / HTML injection basics
    text = text.replace("<", "")
    text = text.replace(">", "")
    text = text.replace("`", "")
 
    # Null byte (can bypass some filters)
    text = text.replace("\x00", "")
 
    return text.strip()
 
