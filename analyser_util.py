def channelIndexFromName(measuredChannel):
    if measuredChannel.lower() == 'red':
        return 0
    if measuredChannel.lower() == 'green':
        return 1
    if measuredChannel.lower() == 'blue':
        return 2
    raise RuntimeError('{} is not a valid channel '
                       'name.'.format(measuredChannel))


