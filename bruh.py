import asyncio as io
import httpx as hx
import aiofiles as iof
from contextvars import ContextVar
from async_lru import alru_cache
from functools import lru_cache
import timeit


class timer:
    @lru_cache(maxsize=None)
    def __init__(self, name=None):
        self.name = " '"  + name + "'" if name else ''

    @lru_cache(maxsize=None)
    def __enter__(self):
        self.start = timeit.default_timer()
    
    @lru_cache(maxsize=None)
    def __exit__(self, exc_type, exc_value, traceback):
        self.took = (timeit.default_timer() - self.start) * 1000.0
        if int(self.took * 1000000.0) < 1000:
            print('Code block' + self.name + ' took: ' + str(self.took * 1000000.0) + ' ns')
            print('congrats')
        elif int(self.took * 1000.0) < 1000:
            print('Code block' + self.name + ' took: ' + str(self.took * 1000.0) + ' μs')
        elif int(self.took) > 1000:
            print('Code block' + self.name + ' took: ' + str(self.took / 1000.0) + ' s')
        else:
            print('Code block' + self.name + ' took: ' + str(self.took) + ' ms')

#url exp: https://www.gravatar.com/avatar/2eeed273cdbbb92e20ab7fdca5110285?s=64&d=identicon&r=PG&f=1

# url = "https://cdn-fastly.obsproject.com/downloads/OBS-Studio-27.2.4-Full-Installer-x64.exe" #big
url = 'https://rpg.ifi.uzh.ch/data/VID2E/pretrained_models.zip'
# url = 'https://cdn140.picsart.com/290674085031201.jpg' #med
fileName = 'pretrained_models.zip'
headers = {'Range':'bytes=-1'}
read = ContextVar("write")
part = 30
startLen = {}

# @lru_cache(maxsize=None)
def writeConcat():
	write = read.get()
	with open(f'~temp{write}', 'rb') as f:
		while True:
			data = f.read(5120000)
			if not data:
				break
			with open(fileName, 'ab') as final:
				final.write(data)
	return True

@alru_cache(maxsize=None)
async def concat():
	async for i in Arange(part).__aiter__():
			read.set(i)
			writeConcat()

async def Arange(start, stop=None, step=1):
    if stop:
        range_ = range(start, stop, step)
    else:
        range_ = range(start)
    for i in range_:
        yield i
        await io.sleep(0)

@alru_cache(maxsize=None)
async def download(index, start, distance):
	async with hx.AsyncClient() as asy:
		try:
			async with asy.stream('GET',url, headers={'Range':f'bytes={start}-{distance-1}'}) as resp:
				if resp.status_code == 200:
					return False
				elif resp.status_code == 206:
					async with iof.open(f'~temp{index}','wb') as cache:
						async for data in resp.aiter_bytes():
							await cache.write(data)
						await io.sleep(0)
					print(f'No {index} download is Complete')
					startLen.update([(index, True)])
					return True
		except:
			await io.create_subprocess_shell('rm ~temp*', stdout=io.subprocess.PIPE, stderr=io.subprocess.PIPE)

@alru_cache(maxsize=None)
async def main(url=url):
	with timer('download'):
		async with hx.AsyncClient() as asy:
			try:
				async with asy.stream('HEAD', url) as cL:
					async for i in Arange(part).__aiter__():
						startLen.update([(i, i * int(cL.headers['content-length'])//part)])
					run = await io.gather(\
						*[\
				            download(index=i, start=startLen[i], distance=startLen[i+1] if i < (part - 1) else int(cL.headers['content-length'])) \
						    async for i in Arange(part).__aiter__()\
				        ]
				    )

			except KeyError:
				async with asy.stream('GET', url, headers={'Range':'bytes=0-1', 'Content-Range':'bytes 0-1/*'}) as cLA:
					async for i in Arange(part).__aiter__():
						startLen.update([(i, i * int(cLA.headers['content-range'].split('/')[1])//part)])
				run = await io.gather(\
					*[\
		                download(index=i, start=startLen[i], distance=startLen[i+1] if i < (part - 1) else int(cLA.headers['content-range'].split('/')[1])) \
					    async for i in Arange(part).__aiter__()\
		            ]
		        )
		        
	with timer('write'):
		while True:
			for _, i in enumerate(list(startLen.values())):
				if type(i) == int:
					stop = False
					await io.sleep(0.25)
					break
				elif _ == part - 1:
					stop = True
					count = 0
			# print(list(startLen.values()))
			if stop == True:
				for i in list(startLen.values()):
					if i == True:
						count += i

				if count == part:
					await concat()
					break


# import nest_asyncio
# nest_asyncio.apply()
# file only
import os
# proses = subprocess.run(['ls'], stdout=subprocess.PIPE)
# print(proses.stdout.decode('ascii'))
if __name__ == '__main__':
	os.system('rm final*')

loop = io.get_event_loop()
loop.run_until_complete(main())
loop.close()

os.system('rm ~temp*')
# subprocess.Popen(['rm', '~temp*'])
#google colab test
# io.run(main())

# io.get_event_loop().run_until_complete(main())
