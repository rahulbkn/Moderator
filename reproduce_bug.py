import asyncio
from main import prepare_image

async def test_prepare_image():
    try:
        # This should fail if prepare_image is async and not awaited
        # The return type will be a coroutine, not a string path
        result = prepare_image("https://example.com/image.jpg")
        print(f"Result type: {type(result)}")
        
        # If it returns a coroutine, calling os.path.exists on it (in finally block)
        # or just treating it as a path will fail.
        
        # Let's try to await it to see what happens
        path = await result
        print(f"Successfully prepared image at: {path}")
    except Exception as e:
        print(f"Caught expected error or unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_prepare_image())
