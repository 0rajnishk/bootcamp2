import asyncio

async def main():
    for i in range(3):
        print(i)
        await asyncio.sleep(5)
    print("done in async")

# Start the event loop manually
loop = asyncio.get_event_loop()

# Create the async task
loop.create_task(main())

# Print "done" immediately
print("done")

# Run the loop until all tasks are completed
loop.run_forever()


