import unittest

from bot import ConversationBot, MockApiClient
from conversation_engine import ConversationEngine, Intent


class ConversationBotTests(unittest.TestCase):
    def test_intent_and_entities_from_natural_message(self) -> None:
        understanding = ConversationEngine().understand(
            "I am Ravi from Ghatol, I have chest pain for two hours"
        )

        self.assertEqual(understanding.intent, Intent.FIND_CARE)
        self.assertEqual(understanding.entities.patient_id, "pat-ravi")
        self.assertEqual(understanding.entities.location, "Ghatol")
        self.assertEqual(understanding.entities.symptoms, "chest pain")
        self.assertEqual(understanding.entities.duration, "two hours")
        self.assertEqual(understanding.missing, [])

    def test_natural_find_care_uses_existing_backend_flow(self) -> None:
        bot = ConversationBot(MockApiClient())

        response = bot.handle(
            "chat",
            "I am Ravi from Ghatol, I have chest pain for two hours",
        )

        self.assertIn("URGENT", response)
        self.assertIn("District Hospital", response)
        self.assertEqual(bot.state("chat").patient_id, "pat-ravi")

    def test_natural_appointment_requires_confirmation_before_booking(self) -> None:
        bot = ConversationBot(MockApiClient())

        response = bot.handle("chat", "Book Ravi for cardiology tomorrow")
        self.assertIn("Available options", response)
        self.assertIn("1.", response)
        confirmation = bot.handle("chat", "1")
        self.assertIn("Confirm booking", confirmation)
        self.assertEqual(bot.api.appointments("pat-ravi"), [])
        booked = bot.handle("chat", "yes")
        self.assertIn("Appointment booked", booked)
        self.assertEqual(len(bot.api.appointments("pat-ravi")), 1)

    def test_natural_appointment_fills_missing_service_and_date(self) -> None:
        bot = ConversationBot(MockApiClient())

        self.assertIn("What service", bot.handle("chat", "I need an appointment tomorrow"))
        self.assertIn("Which date", bot.handle("chat", "cardiology"))
        self.assertIn("Available options", bot.handle("chat", "tomorrow"))

    def test_natural_referral_status_uses_backend_state(self) -> None:
        bot = ConversationBot(MockApiClient())

        response = bot.handle("chat", "What happened to my referral?")
        self.assertIn("District Hospital, Udaipur", response)
        self.assertIn("Status: created", response)
        self.assertIn("Journey", response)

    def test_follow_up_referral_status_explains_next_action(self) -> None:
        bot = ConversationBot(MockApiClient())
        bot.api._referral["state"] = "follow_up"
        response = bot.handle("chat", "What happened to my referral?")
        self.assertIn("complete the generated follow-up", response)

    def test_natural_followup_status_and_confirmation(self) -> None:
        bot = ConversationBot(MockApiClient())

        response = bot.handle("chat", "Do I have any follow-ups?")
        self.assertIn("Blood-pressure follow-up", response)
        self.assertIn("due", response)

        confirm = bot.handle("chat", "I completed my follow-up")
        self.assertIn("Mark Ravi's follow-up", confirm)

        completed = bot.handle("chat", "yes")
        self.assertIn("Follow-up marked completed", completed)

    def test_mock_find_care_creates_referral_and_completes_followup(self) -> None:
        bot = ConversationBot(MockApiClient())

        self.assertIn("Find Care", bot.handle("chat", "/start"))
        bot.handle("chat", "1")
        triage = bot.handle("chat", "chest pain")
        self.assertIn("URGENT", triage)
        self.assertIn("District Hospital", triage)
        self.assertIn("Why this facility?", bot.handle("chat", "1"))
        self.assertIn("Referral created", bot.handle("chat", "referral"))
        self.assertIn("due", bot.handle("chat", "4"))
        self.assertIn("completed", bot.handle("chat", "complete"))

    def test_emergency_guidance_stops_flow(self) -> None:
        bot = ConversationBot(MockApiClient())
        bot.handle("chat", "/start")
        bot.handle("chat", "1")
        response = bot.handle("chat", "unconscious")
        self.assertIn("immediate human/emergency care", response)


if __name__ == "__main__":
    unittest.main()
