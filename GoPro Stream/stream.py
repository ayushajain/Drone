from goprohero import GoProHero
camera = GoProHero(password='password')
camera.command('record', 'on')
status = camera.status()
