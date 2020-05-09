tiers = {}
tiers['Platinum'] = 0
tiers['Gold'] = 1
tiers['Silver'] = 2
tiers['Bronze'] = 3
tiers['Carbon'] = 4


def is_below(ta, tb):
    try:
        is_it =  tiers[ta] > tiers[tb]
    except KeyError:
        print("invalid tier key in comparison")
        return False

    return is_it