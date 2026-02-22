from datetime import datetime

from src.app.models.models import ArticleRecord, XPostRecord


X_POSTS: list[XPostRecord] = [
    XPostRecord(
        id="x1",
        url="https://x.com/consciousphilos/status/1968904800218562608",
        text="""America is a golden calf and we'll suck it dry, chop it up, and sell it off piece by piece until there is nothing left but the world's biggest welfare state that we'll create and control... This is what we do to countries that we hate. We destroy them very slowly" - Netanyahu""",
        media_url="https://pbs.twimg.com/media/G1L0enNXoAA2mMy?format=jpg&name=medium",
        created_at=datetime(2025, 12, 21, 11, 15, 00)
    ),
    XPostRecord(
        id="x2",
        url="https://x.com/F_W_Steingeier/status/1870387777201913901",
        text="""
        Die tatbegehende Person in #Magdeburg war rechtsradikal. Das zeigt ein doppeltes Versagen der Gesellschaft: 
        Wir waren unfähig, diese Person in Deutschland willkommen zu heißen und sie von demokratischen Werten zu überzeugen. 
        Der Kampf gegen Rechts muss weitergehen.
        """,
        media_url="https://pbs.twimg.com/media/GfTzsGDWoAECX42?format=jpg&name=900x900",
        created_at=datetime(2025, 12, 21, 12, 34, 28)
    ),

    XPostRecord(
        id="x3",
        url="https://x.com/atrupar/status/2013978220735950986",
        text="""Trump on NATO: "We never ask for anything, and we never got anything. We probably won't get anything unless I decide to use excessive strength and force, where we would be frankly unstoppable. But I won't do that. Okay?""",
        media_url=None,
        created_at=datetime(2026, 1, 22, 12, 34, 28)
    ),
]
