from .seed_companies import seed_companies
from .seed_regions import seed_regions
from .seed_deal_branches import seed_deal_branches
from .seed_deal_details import seed_deal_details
from .seed_deal_types import seed_deal_types
from .seed_users import seed_users
from .seed_deals import seed_deals
from .seed_deal_consumers import seed_deal_consumers
from .seed_feedbacks import seed_feedback

async def run_all_seeds():
    # 1. Сначала базовые справочники
    await seed_regions()
    await seed_deal_branches()
    await seed_deal_details()
    await seed_deal_types()

    # 2. Затем сущности, которые зависят от справочников
    await seed_companies()
    await seed_users()
    await seed_deals()
    await seed_deal_consumers()
    await seed_feedback()