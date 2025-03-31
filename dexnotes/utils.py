def parse_date(date_str):
    from datetime import datetime
    return datetime.fromisoformat(date_str).isoformat()

def format_tags(tags_str):
    return tags_str.split(',') if tags_str else []