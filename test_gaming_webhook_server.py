
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:11:50
# Last Updated: 2025-12-18T12:28:34
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
This script simulates a casino platform that sends registration and deposit webhooks to your tracker server.

It's designed so that even beginners can easily understand how the steps work.

How it works:
- The script can automatically simulate typical casino activity (users registering and depositing).
- You can also test it manually: run and choose what kind of webhook to send.
"""

import asyncio
import aiohttp
import uuid
from datetime import datetime
from loguru import logger

class GamingWebhookSimulator:
    """
    This class handles sending webhooks (registration and deposit) to the tracker server.
    It opens an HTTP session and provides methods to send webhooks.
    """

    def __init__(self, tracker_url: str = "http://localhost:5000"):
        # The base URL of the tracker server (where webhooks will be sent)
        self.tracker_url = tracker_url
        self.session = None

    async def __aenter__(self):
        # Initialize the HTTP session for making requests
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Properly close the session to clean up resources
        if self.session:
            await self.session.close()

    async def send_deposit_webhook(self, deposit_data: dict) -> dict:
        """
        Sends a deposit webhook to the tracker.

        deposit_data should contain:
          - user_id, amount, currency, transaction_id, platform, game_type, payment_method, is_first_deposit, timestamp
        """
        url = f"{self.tracker_url}/webhooks/gaming/deposit"
        logger.info(f"Sending deposit webhook: {deposit_data.get('transaction_id')}")

        try:
            async with self.session.post(url, json=deposit_data) as response:
                result = await response.json()
                logger.info(f"Deposit response: {response.status} - {result}")
                return result
        except Exception as e:
            logger.error(f"Failed to send deposit webhook: {e}")
            return {"error": str(e)}

    async def send_registration_webhook(self, registration_data: dict) -> dict:
        """
        Sends a registration webhook to the tracker.

        registration_data should contain:
          - user_id, platform, registration_method, country, timestamp
        """
        url = f"{self.tracker_url}/webhooks/gaming/registration"
        logger.info(f"Sending registration webhook: {registration_data.get('user_id')}")

        try:
            async with self.session.post(url, json=registration_data) as response:
                result = await response.json()
                logger.info(f"Registration response: {response.status} - {result}")
                return result
        except Exception as e:
            logger.error(f"Failed to send registration webhook: {e}")
            return {"error": str(e)}

async def simulate_gaming_activity():
    """
    Simulates a sequence of typical gaming platform user activity, step by step.
    1. Several users register.
    2. Some of them make deposits.
    3. For deposits, both first and repeat deposits are simulated.
    """
    logger.info("Starting gaming platform simulation...")

    async with GamingWebhookSimulator() as simulator:
        # Step 1: User registrations.
        logger.info("Simulating user registrations...")
        users = ["user_d048a73d", "user_762add60", "user_93e9ea77", "user_315ee12a", "user_a39b55fa"]

        for user_id in users:
            registration_data = {
                "user_id": user_id,
                "platform": "casino_pro",
                "registration_method": "email",
                "country": "US",
                "timestamp": datetime.utcnow().isoformat()
            }
            await simulator.send_registration_webhook(registration_data)
            await asyncio.sleep(0.5)  # Short pause between registrations to mimic real-world flow

        # Step 2: Simulate deposits for some users (not all registrants become depositors)
        logger.info("Simulating deposits...")
        depositing_users = users[:3]  # Choose some users for making deposits

        games = ["slots", "blackjack", "roulette", "poker", "baccarat"]
        payment_methods = ["credit_card", "paypal", "crypto", "bank_transfer"]

        for user_id in depositing_users:
            num_deposits = 2  # Each selected user makes 2 deposits

            for deposit_num in range(num_deposits):
                # Prepare unique transaction ID for each deposit
                transaction_id = f"tx_{uuid.uuid4().hex[:12]}"
                deposit_data = {
                    "user_id": user_id,
                    "amount": 50.0 + (deposit_num * 25.0),  # 50 for first, 75 for second
                    "currency": "USD",
                    "transaction_id": transaction_id,
                    "platform": "casino_pro",
                    "game_type": games[deposit_num % len(games)],
                    "payment_method": payment_methods[deposit_num % len(payment_methods)],
                    "is_first_deposit": deposit_num == 0,
                    "timestamp": datetime.utcnow().isoformat()
                }

                await simulator.send_deposit_webhook(deposit_data)

                # Step 3: For first deposit, notify that CPA should be calculated
                if deposit_data["is_first_deposit"]:
                    logger.info(f"First deposit for {user_id} - CPA calculation expected.")

                await asyncio.sleep(1.0)  # Pause between deposits

        logger.info("Gaming platform simulation completed.")
        logger.info(f"Summary: {len(users)} registrations, {len(depositing_users) * 2} deposits.")

async def run_interactive_test():
    """
    Allows the user to send webhooks manually for testing.

    For each run, you can:
    1. Register a user
    2. Make a first deposit
    3. Make a repeat deposit
    4. Run the full simulation (all users, all steps)
    5. Exit
    """
    logger.info("Interactive Gaming Webhook Test Server")
    logger.info("------------------------------------------")

    async with GamingWebhookSimulator() as simulator:
        while True:
            print("\nChoose test scenario:")
            print("1. Send user registration")
            print("2. Send user deposit (first)")
            print("3. Send user deposit (repeat)")
            print("4. Run full simulation")
            print("5. Exit")

            choice = input("\nEnter choice (1-5): ").strip()

            if choice == "1":
                # Send a registration webhook
                user_id = input("User ID: ").strip() or f"user_{uuid.uuid4().hex[:8]}"
                registration_data = {
                    "user_id": user_id,
                    "platform": "casino_pro",
                    "registration_method": "email",
                    "country": "US",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await simulator.send_registration_webhook(registration_data)

            elif choice == "2":
                # Send a first deposit (CPA counted)
                user_id = input("User ID: ").strip()
                try:
                    amount = float(input("Deposit amount: ").strip() or "100.0")
                except ValueError:
                    print("Invalid amount, using 100.0")
                    amount = 100.0
                transaction_id = f"tx_{uuid.uuid4().hex[:12]}"
                deposit_data = {
                    "user_id": user_id,
                    "amount": amount,
                    "currency": "USD",
                    "transaction_id": transaction_id,
                    "platform": "casino_pro",
                    "game_type": "slots",
                    "payment_method": "credit_card",
                    "is_first_deposit": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
                result = await simulator.send_deposit_webhook(deposit_data)
                if result.get("status") == "success":
                    logger.success("First deposit processed, CPA should be calculated.")

            elif choice == "3":
                # Send a repeat deposit (CPA not counted)
                user_id = input("User ID: ").strip()
                try:
                    amount = float(input("Deposit amount: ").strip() or "50.0")
                except ValueError:
                    print("Invalid amount, using 50.0")
                    amount = 50.0
                transaction_id = f"tx_{uuid.uuid4().hex[:12]}"
                deposit_data = {
                    "user_id": user_id,
                    "amount": amount,
                    "currency": "USD",
                    "transaction_id": transaction_id,
                    "platform": "casino_pro",
                    "game_type": "blackjack",
                    "payment_method": "paypal",
                    "is_first_deposit": False,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await simulator.send_deposit_webhook(deposit_data)

            elif choice == "4":
                # Run the full, automatic simulation (recommended for basic testing)
                await simulate_gaming_activity()

            elif choice == "5":
                logger.info("Goodbye.")
                break

            else:
                print("Invalid choice. Try again.")

def main():
    """
    Program entry point.
    Parses command-line arguments and runs either full-auto or interactive mode.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Gaming Webhook Test Server")
    parser.add_argument("--tracker-url", default="http://localhost:5000",
                        help="Tracker API URL")
    parser.add_argument("--auto", action="store_true",
                        help="Run automatic simulation of gaming activity")
    parser.add_argument("--interactive", action="store_true",
                        help="Run in interactive manual testing mode")

    args = parser.parse_args()

    # Configure the logger output to be readable for terminal
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:HH:mm:ss} | {level: <8} | {message}",
        level="INFO"
    )

    async def run():
        # If --auto is specified, run the basic simulation automatically
        if args.auto:
            async with GamingWebhookSimulator(args.tracker_url) as simulator:
                await simulate_gaming_activity()
        # If --interactive is specified, allow manual step-by-step testing
        elif args.interactive:
            await run_interactive_test()
        # If neither, print usage and exit
        else:
            print("Usage: python test_gaming_webhook_server.py [--auto | --interactive] [--tracker-url URL]\n")
            print("Examples:")
            print("  python test_gaming_webhook_server.py --auto")
            print("  python test_gaming_webhook_server.py --interactive")
            print("  python test_gaming_webhook_server.py --auto --tracker-url http://localhost:3000")

    asyncio.run(run())

if __name__ == "__main__":
    main()