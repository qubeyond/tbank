import asyncio
import aiohttp

async def test_websocket_direct():
    try:
        async with aiohttp.ClientSession() as session:
            print("Testing WebSocket connection...")
            async with session.ws_connect("ws://localhost:8000/api/notifications/ws/test_session_123") as ws:
                print("✅ WebSocket connected successfully!")
                
                # Ждем приветственные нотификации
                try:
                    welcome_msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
                    print(f"✅ Received message: {welcome_msg}")
                except asyncio.TimeoutError:
                    print("ℹ️  No welcome message received")
                
                # Тестируем ping-pong
                await ws.send_str("ping")
                pong_msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
                print(f"✅ Ping-pong test: {pong_msg}")
                
                # Держим соединение
                await asyncio.sleep(1)
                print("✅ WebSocket test completed successfully!")
                return True
                
    except asyncio.TimeoutError:
        print("❌ WebSocket timeout - endpoint might not be responding")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket_direct())
    exit(0 if success else 1)