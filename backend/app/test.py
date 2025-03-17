import time
import asyncio

async def main():
    for i in range(3):
        print(i)
        await asyncio.sleep(5)

    print("done in async")

s =  asyncio.run(main())

print("done")

