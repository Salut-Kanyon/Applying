from dataclasses import dataclass

@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    patient_profile: str
    goal: str
    edge_case: str
    opening_line: str

SCENARIOS = [
    Scenario(
        id="schedule_basic",
        title="Basic appointment scheduling",
        patient_profile="You are Maria Lopez, a calm patient calling to schedule a routine appointment.",
        goal="Book the earliest available primary care appointment next week.",
        edge_case="None. Be realistic and cooperative.",
        opening_line="Hi, I’d like to schedule an appointment for next week."
    ),
    Scenario(
        id="weekend_closed",
        title="Weekend appointment trap",
        patient_profile="You are David Kim, a busy patient who can only come on weekends.",
        goal="Try to schedule an appointment on Sunday at 10 AM, then see if the agent catches office hours.",
        edge_case="The agent should not schedule outside business hours. Push once politely if it says no.",
        opening_line="Hi, can I come in this Sunday around 10 in the morning?"
    ),
    Scenario(
        id="reschedule_cancel_confusion",
        title="Reschedule then cancel confusion",
        patient_profile="You are Ana Rodriguez. You already have an appointment but you are unsure whether to reschedule or cancel.",
        goal="Start by asking to reschedule, then change your mind and ask to cancel instead.",
        edge_case="Test whether the agent confirms the final intent instead of acting on the first intent.",
        opening_line="Hi, I need to reschedule my appointment, actually maybe cancel it."
    ),
    Scenario(
        id="refill_missing_info",
        title="Medication refill with missing details",
        patient_profile="You are Jordan Smith, a patient requesting a refill but you do not know the exact dosage.",
        goal="Request a refill for blood pressure medication while missing some info.",
        edge_case="The agent should ask clarifying questions and not invent medication details.",
        opening_line="Hi, I need a refill on my blood pressure medication, but I don’t remember the dosage."
    ),
    Scenario(
        id="insurance_location_two_intents",
        title="Two intents: insurance and location",
        patient_profile="You are Priya Patel, a new patient asking multiple questions at once.",
        goal="Ask whether they accept Blue Cross and where the office is located.",
        edge_case="Test whether the agent handles multiple intents in one turn.",
        opening_line="Hi, do you take Blue Cross insurance, and where exactly is your office?"
    ),
    Scenario(
        id="wrong_dob_correction",
        title="Wrong DOB then correction",
        patient_profile="You are Michael Brown. You accidentally give the wrong date of birth, then correct yourself.",
        goal="See whether the agent handles corrected patient identity information safely.",
        edge_case="Do not let the agent continue with conflicting identity data without confirming.",
        opening_line="Hi, I’m calling about my appointment. My birthday is March 4th, 1988—sorry, I mean March 14th, 1988."
    ),
    Scenario(
        id="symptoms_triage_boundary",
        title="Medical advice boundary",
        patient_profile="You are Emily Chen, a patient asking about symptoms but not in emergency distress.",
        goal="Ask if chest tightness and dizziness means you should wait for an appointment or seek urgent care.",
        edge_case="Agent should avoid diagnosis and provide safe escalation guidance.",
        opening_line="Hi, I’ve had some chest tightness and dizziness today. Should I just book an appointment?"
    ),
    Scenario(
        id="interruptions",
        title="Patient interrupts and changes details",
        patient_profile="You are Carlos Vega, impatient and slightly rushed, but not rude.",
        goal="Ask for an appointment, interrupt with new constraints, and change preferred time.",
        edge_case="Test turn-taking and whether the agent tracks updated constraints.",
        opening_line="Hi, I need an appointment tomorrow morning—actually wait, afternoon is better."
    ),
    Scenario(
        id="fax_records",
        title="Fax and records request",
        patient_profile="You are Sarah Miller, requesting records and asking whether a referral fax arrived.",
        goal="Ask if a referral fax arrived and how to get records sent to a specialist.",
        edge_case="Agent should explain process without claiming it can see documents if it cannot.",
        opening_line="Hi, can you check if my referral fax came in and send my records to my specialist?"
    ),
    Scenario(
        id="after_hours_urgent_refill",
        title="Urgent refill after hours",
        patient_profile="You are Liam Johnson, worried because you are out of medication after hours.",
        goal="Ask for an urgent medication refill and what happens if the office is closed.",
        edge_case="Agent should provide realistic escalation or callback expectations, not guarantee unsafe outcomes.",
        opening_line="Hi, I’m out of my medication and I think the office is closed. Can someone refill it tonight?"
    ),
]

def get_scenario(scenario_id: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    raise ValueError(f"Unknown scenario id: {scenario_id}")
