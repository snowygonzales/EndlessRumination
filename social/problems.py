"""Curated pool of relatable everyday problems for social media takes.

These problems are designed to resonate with the target audience (young
professionals, anxious millennials/Gen-Z) and produce engaging, shareable
AI perspectives from the app's 40 personas.
"""
from __future__ import annotations

import random

PROBLEMS: list[str] = [
    # Work anxiety
    "I sent a passive-aggressive email to a recruiter after bombing an interview and now I can't stop replaying it",
    "I've been at my job for two years and I still feel like an impostor who's about to be found out",
    "My boss gave me vague feedback and now I'm spiraling about whether I'm about to get fired",
    "I completely blanked during a presentation in front of the entire department",
    "I accidentally replied-all with a snarky comment about the meeting organizer",
    "I got passed over for a promotion and I'm pretending I don't care but I absolutely do",
    "I called in sick to have a mental health day but then ran into my coworker at the grocery store",

    # Social embarrassment
    "I said something awkward at a party last weekend and now I keep thinking about it at 3am",
    "I waved back at someone who was waving at the person behind me and I want to disappear",
    "I've been pronouncing my coworker's name wrong for six months and just found out",
    "I sent a text complaining about someone to that exact person by mistake",
    "I laughed at something that wasn't a joke in a group conversation and everyone just stared",
    "I accidentally liked my ex's Instagram photo from three years ago while stalking their profile",

    # Relationship friction
    "My partner and I had a stupid argument about dishes and now neither of us will apologize first",
    "I ghosted someone I was dating and now I feel terrible but it's been too long to reach out",
    "My best friend got promoted and I'm happy for them but also weirdly jealous and I hate myself for it",
    "I realized I'm the toxic one in my friend group and I don't know how to change",
    "My parents keep comparing me to my sibling who has their life together and I'm falling apart",
    "I snapped at my partner over something tiny and now I feel like the worst person alive",

    # Financial stress
    "I spent $200 on clothes I don't need because I was stressed and now I'm more stressed",
    "I've been avoiding looking at my bank account for three weeks and I know it's bad",
    "All my friends are buying houses and I can barely afford rent",
    "I impulse-subscribed to six different apps this month and I use none of them",

    # FOMO / comparison
    "I compared my life to my college roommate's Instagram and now I feel like a failure",
    "Everyone I know seems to have a clear career path and I'm just winging it",
    "I skipped a friend's wedding because of social anxiety and now I feel guilty and left out",
    "I keep seeing people my age doing incredible things and I can't even keep a plant alive",

    # Procrastination
    "I've been doom-scrolling for three hours instead of working on a project that's due tomorrow",
    "I have a deadline in two hours and I'm reorganizing my desk for the fourth time",
    "I told myself I'd start the gym this month and it's now the 28th",
    "I keep adding things to my to-do list instead of actually doing any of them",

    # Existential dread
    "I turned 30 and suddenly every life choice I've ever made feels like a mistake",
    "I woke up at 2am and googled 'am I wasting my life' for forty-five minutes",
    "I've been thinking about how everyone I know is going to die someday and I can't stop",
    "I don't know what I want to do with my life and I'm running out of time to figure it out",

    # Health worry
    "I googled my symptoms and now I'm convinced I have a rare tropical disease",
    "I haven't slept more than five hours in a week and my eye won't stop twitching",
    "I keep canceling therapy appointments because I feel anxious about going to therapy",

    # Family tension
    "My family group chat is a war zone and I'm getting dragged into everyone's drama",
    "My mom keeps asking when I'm having kids and I can barely take care of myself",
    "I found out my family has been talking about me behind my back at holiday dinners",

    # Creative block / purpose
    "I used to love painting and now I can't even pick up a brush without feeling like a fraud",
    "I quit my stable job to follow my passion and now I'm terrified I made a huge mistake",
    "I started a side project six months ago and haven't touched it since day three",
]


def pick_random_problem() -> str:
    """Return a random problem from the curated pool."""
    return random.choice(PROBLEMS)


def pick_random_problems(count: int = 1) -> list[str]:
    """Return N unique random problems."""
    return random.sample(PROBLEMS, min(count, len(PROBLEMS)))
