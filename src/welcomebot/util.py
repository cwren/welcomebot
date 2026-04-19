async def update_group (logger, bot, context, store):
    logger.info("updating group information")
    post_group = bot.get_group(context.message.group)
    prev_members = store.get_members(context.message.group)
    new_member = False
    if prev_members:
        for member in post_group["members"]:
            logger.debug(f'  looking for {member} in old group')
            if member not in prev_members:
                logger.debug("  found a new member of the group")
                new_member = True
        for member in prev_members:
            logger.debug(f'  looking for {member} in new group')
            if member not in post_group["members"]:
                logger.debug("  a member left the group")
    else:
        logger.debug("  found a new group")
        # TODO post introduction

    # update member cache
    store.put_members(context.message.group, post_group["members"])
    valid_group_ids = [ g["internal_id"] for g in bot.groups ]
    store.retain_only(valid_group_ids)

    return new_member
