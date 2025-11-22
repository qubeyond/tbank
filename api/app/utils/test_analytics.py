import aiohttp
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_analytics():
    print("Starting analytics test...")
    
    # 1. Authentication
    login_data = {
        "username": "superadmin", 
        "password": "superadmin123"
    }
    
    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            print(f"Login status: {response.status}")
            
            if response.status != 200:
                error_text = await response.text()
                print(f"Auth error: {error_text}")
                return
            
            token_data = await response.json()
            access_token = token_data["access_token"]
            print(f"Token received: {access_token}")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 2. Create test data
        event_data = {
            "name": "Test event for analytics",
            "is_active": True
        }
        
        async with session.post(f"{BASE_URL}/event/", json=event_data, headers=headers) as response:
            print(f"Create event status: {response.status}")
            
            if response.status != 201:
                error_text = await response.text()
                print(f"Event creation error: {error_text}")
                return
            
            event = await response.json()
            event_id = event["id"]
            event_code = event["code"]
            print(f"Event created ID: {event_id}, Code: {event_code}")
        
        # 3. Create queue
        queue_data = {
            "event_id": event_id,
            "is_active": True
        }
        
        async with session.post(f"{BASE_URL}/queue/", json=queue_data, headers=headers) as response:
            print(f"Create queue status: {response.status}")
            
            if response.status != 201:
                error_text = await response.text()
                print(f"Queue creation error: {error_text}")
                return
            
            queue = await response.json()
            queue_id = queue["id"]
            print(f"Queue created ID: {queue_id}")
        
        # 4. Create tickets
        tickets_created = []
        for i in range(3):
            ticket_data = {
                "event_code": event_code,
                "session_id": f"test_session_{i}",
                "notes": f"Test ticket {i} for analytics"
            }
            
            async with session.post(f"{BASE_URL}/ticket/", json=ticket_data) as response:
                print(f"Create ticket {i+1} status: {response.status}")
                
                if response.status == 201:
                    ticket = await response.json()
                    tickets_created.append(ticket["id"])
                    print(f"Ticket created ID: {ticket['id']}")
                else:
                    error_text = await response.text()
                    print(f"Ticket creation error: {error_text}")
        
        if not tickets_created:
            print("No tickets created")
            return
        
        ticket_id = tickets_created[0]
        
        await asyncio.sleep(1)
        
        print(f"Test IDs: event_id={event_id}, queue_id={queue_id}, ticket_id={ticket_id}")
        
        # TEST EVENT ANALYTICS
        print("\nTesting event analytics...")
        
        # 1. Event basic stats
        async with session.get(f"{BASE_URL}/analytics/event/{event_id}/basic", headers=headers) as response:
            print(f"Event basic stats status: {response.status}")
            
            if response.status == 200:
                basic_stats = await response.json()
                print(f"Basic stats - ID: {basic_stats.get('event_id')}, Tickets: {basic_stats.get('total_tickets')}, Completed: {basic_stats.get('completed_tickets')}")
            else:
                error_text = await response.text()
                print(f"Basic stats error: {error_text}")
        
        # 2. Event detailed stats
        async with session.get(f"{BASE_URL}/analytics/event/{event_id}/detailed", headers=headers) as response:
            print(f"Event detailed stats status: {response.status}")
            
            if response.status == 200:
                detailed_stats = await response.json()
                print(f"Detailed stats - Queues: {detailed_stats.get('queues_count')}, Active tickets: {detailed_stats.get('active_tickets')}")
            else:
                error_text = await response.text()
                print(f"Detailed stats error: {error_text}")
        
        # 3. Events overview
        async with session.get(f"{BASE_URL}/analytics/event/overview", headers=headers) as response:
            print(f"Events overview status: {response.status}")
            
            if response.status == 200:
                overview = await response.json()
                events_count = len(overview.get('events', []))
                print(f"Events overview: {events_count} events found")
            else:
                error_text = await response.text()
                print(f"Events overview error: {error_text}")
        
        # TEST QUEUE ANALYTICS
        print("\nTesting queue analytics...")
        
        # 1. Queue basic stats
        async with session.get(f"{BASE_URL}/analytics/queue/{queue_id}/basic", headers=headers) as response:
            print(f"Queue basic stats status: {response.status}")
            
            if response.status == 200:
                queue_basic = await response.json()
                print(f"Queue basic - Position: {queue_basic.get('current_position')}, Waiting: {queue_basic.get('waiting_count')}")
            else:
                error_text = await response.text()
                print(f"Queue basic stats error: {error_text}")
        
        # 2. Queue performance
        async with session.get(f"{BASE_URL}/analytics/queue/{queue_id}/performance", headers=headers) as response:
            print(f"Queue performance status: {response.status}")
            
            if response.status == 200:
                queue_perf = await response.json()
                print(f"Queue performance - Avg service: {queue_perf.get('avg_service_time_seconds')}s, Avg wait: {queue_perf.get('avg_wait_time_seconds')}s")
            else:
                error_text = await response.text()
                print(f"Queue performance error: {error_text}")
        
        # 3. Queues overview
        async with session.get(f"{BASE_URL}/analytics/queue/event/{event_id}/overview", headers=headers) as response:
            print(f"Queues overview status: {response.status}")
            
            if response.status == 200:
                queues_overview = await response.json()
                queues_count = len(queues_overview.get('queues', []))
                print(f"Queues overview: {queues_count} queues found")
            else:
                error_text = await response.text()
                print(f"Queues overview error: {error_text}")
        
        # TEST TICKET ANALYTICS
        print("\nTesting ticket analytics...")
        
        # 1. Ticket stats
        async with session.get(f"{BASE_URL}/analytics/ticket/{ticket_id}/stats", headers=headers) as response:
            print(f"Ticket stats status: {response.status}")
            
            if response.status == 200:
                ticket_stats = await response.json()
                print(f"Ticket stats - Position: {ticket_stats.get('position')}, Status: {ticket_stats.get('status')}")
            else:
                error_text = await response.text()
                print(f"Ticket stats error: {error_text}")
        
        # 2. Tickets timeline
        async with session.get(f"{BASE_URL}/analytics/ticket/queue/{queue_id}/timeline", headers=headers) as response:
            print(f"Tickets timeline status: {response.status}")
            
            if response.status == 200:
                timeline = await response.json()
                tickets_count = len(timeline.get('tickets', []))
                print(f"Tickets timeline: {tickets_count} tickets found")
            else:
                error_text = await response.text()
                print(f"Tickets timeline error: {error_text}")
        
        # 3. Queue tickets stats
        async with session.get(f"{BASE_URL}/analytics/ticket/queue/{queue_id}/stats", headers=headers) as response:
            print(f"Queue tickets stats status: {response.status}")
            
            if response.status == 200:
                queue_tickets_stats = await response.json()
                print(f"Queue tickets stats - Total: {queue_tickets_stats.get('total_tickets')}")
            else:
                error_text = await response.text()
                print(f"Queue tickets stats error: {error_text}")
        
        print("\nAnalytics test completed!")
        
        # Cleanup
        print("\nCleaning up test data...")
        
        delete_data = {"hard_delete": False}
        async with session.delete(f"{BASE_URL}/event/{event_id}", json=delete_data, headers=headers) as response:
            print(f"Delete event status: {response.status}")
            
            if response.status == 200:
                print("Test data cleaned up")
            else:
                error_text = await response.text()
                print(f"Cleanup error: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_analytics())