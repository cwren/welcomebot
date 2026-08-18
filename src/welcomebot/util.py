async def update_group (logger, bot, group, store):
    logger.info("updating group information")
    new_member = False
    post_group = bot.groups.get(group)
    if post_group.members:
        prev_members = store.get_members(group)
        new_member = False
        if prev_members:
            for member in post_group.members:
                logger.debug(f'  looking for {member} in old group')
                if member not in prev_members:
                    logger.debug("  found a new member of the group")
                    new_member = True
            for member in prev_members:
                logger.debug(f'  looking for {member} in new group')
                if member not in post_group.members:
                    logger.debug("  a member left the group")
        else:
            logger.debug("  found a new group")
            # TODO post introduction

        # update member cache
        store.put_members(group, post_group.members)

    logger.info("purging obsolete groups")
    valid_group_ids = [ g.internal_id for g in bot.groups ]
    store.retain_only(valid_group_ids)

    return new_member
