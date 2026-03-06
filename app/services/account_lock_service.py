from sqlalchemy import text


def lock_account(db, account_id):

    db.execute(
        text(
            """
            SELECT id
            FROM account
            WHERE id = :id
            FOR UPDATE
            """
        ),
        {"id": account_id},
    )
