blacklist = ["scam_user1", "scam_user2"]  # Расширь БД

def check_seller(seller_name: str) -> bool:
    return seller_name.lower() not in [s.lower() for s in blacklist]