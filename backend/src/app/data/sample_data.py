from datetime import datetime

from src.app.models.models import ArticleRecord, XPostRecord


X_POSTS: list[XPostRecord] = [
    XPostRecord(
        id="x1",
        handle="@exampleUser1",
        display_name="Example User 1",
        text="First X post",
        created_at=datetime(2025, 12, 21, 11, 15, 00)
    ),
    XPostRecord(
        id="x2",
        handle="@exampleUser2",
        display_name="Example User 2",
        text="Second X post",
        created_at=datetime(2025, 12, 21, 12, 34, 28)
    ),
]
