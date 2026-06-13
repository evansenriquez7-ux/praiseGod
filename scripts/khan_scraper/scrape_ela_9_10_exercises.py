"""
scrape_ela_9_10_exercises.py

Scrapes full exercise content (passage + questions + answer choices) for all
grade 9-10 ELA exercises on Khan Academy: RL.9-10, RI.9-10, L.9-10

Strategy:
- Visit each exercise page with Playwright
- Intercept GraphQL responses (getAssessmentItemById, getInitialDataForPrePhantomUser)
  to capture all Perseus item JSON as KA loads them
- Click Skip (force=True) 3x to trigger all 4 question loads
- Parse itemDataAnswerless from each response (double-encoded JSON)
- Separate passage item from question items
- Save one JSON per exercise to output/ela_9_10_templates/

Output per file (output/ela_9_10_templates/{slug}.json):
{
  "title": "...",
  "url": "...",
  "ccss_standard": "RL.9-10",
  "slug": "...",
  "passage": {
    "title": "...",
    "author": "...",
    "text": "..."
  },
  "questions": [
    {
      "item_id": "...",
      "question_content": "...",
      "widget_type": "radio",
      "choices": [{"label": "A", "content": "..."}]
    }
  ]
}
"""

import asyncio
import json
import re
import time
from pathlib import Path

from playwright.async_api import async_playwright

# All 86 exercises from the scraped standards pages
EXERCISES = {
    "RL.9-10": [
        {"title": "A Doll's House", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-crossing-the-line-indiana/e/a-doll-s-house"},
        {"title": "A Thousand Splendid Suns", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-ties-that-bind-indiana/e/a-thousand-splendid-suns-10"},
        {"title": "Atalanta", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-thriving-indiana/e/atalanta"},
        {"title": "Haroun and the Sea of Stories", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-literary-texts-9/e/haroun-and-the-sea-of-stories"},
        {"title": "Inferences (9th grade Indiana)", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:making-inferences-9-indiana/e/inferences-9"},
        {"title": "Inferences (9th grade)", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-literary-texts-9/e/inferences-9-v2"},
        {"title": "Legendborn", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-thriving-indiana/e/legendborn"},
        {"title": "Musée de Beaux Arts & Landscape with the Fall of Icarus", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-literary-texts-9/e/musee-de-beaux-arts-landscape-with-the-fall-of-icarus"},
        {"title": "Sense and Sensibility", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-literary-texts-bridging-the-gap-9-indiana/e/sense-and-sensibility"},
        {"title": "Text evidence (RL)", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-literary-texts-9/e/text-evidence-9"},
        {"title": "The Absolutely True Diary of a Part-Time Indian", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-literary-texts-bridging-the-gap-9-indiana/e/the-absolutely-true-diary-of-a-part-time-indian"},
        {"title": "The House on Mango Street", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-crossing-the-line-indiana/e/the-house-on-mango-street"},
        {"title": "The Kite Runner", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-into-the-unknown-indiana/e/the-kite-runner"},
        {"title": "The Lottery", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-ties-that-bind-indiana/e/the-lottery"},
        {"title": "The Raven", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-literary-texts-9/e/the-raven"},
        {"title": "The Things They Carried", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-into-the-unknown-indiana/e/the-things-they-carried"},
        {"title": "To Kill a Mockingbird", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-literary-texts-9/e/to-kill-a-mockingbird-9"},
        {"title": "Vocabulary in context (RL)", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-literary-texts-9/e/vocabulary-in-context-9"},
        {"title": "A Midsummer Night's Dream", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-into-the-unknown-indiana/e/a-midsummer-night-s-dream"},
        {"title": "An Ember in the Ashes", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-thriving-indiana/e/an-ember-in-the-ashes"},
        {"title": "Antigone", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-ties-that-bind-indiana/e/antigone"},
        {"title": "Beowulf", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-literary-texts-bridging-the-gap-9-indiana/e/beowulf"},
        {"title": "Children of Blood and Bone", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-crossing-the-line-indiana/e/children-of-blood-and-bone"},
        {"title": "Fahrenheit 451", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-into-the-unknown-indiana/e/fahrenheit-451"},
        {"title": "Romeo and Juliet", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-thriving-indiana/e/romeo-and-juliet"},
        {"title": "The Alchemist", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-ties-that-bind-indiana/e/the-alchemist"},
        {"title": "The Outsiders", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-crossing-the-line-indiana/e/the-outsiders"},
        {"title": "The Sun is Also a Star", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-literary-texts-9/e/the-sun-is-also-a-star"},
        {"title": "Things Fall Apart", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-into-the-unknown-indiana/e/things-fall-apart"},
        {"title": "Throne of Glass", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-literary-texts-thriving-indiana/e/throne-of-glass"},
        {"title": "Tuck Everlasting", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-ties-that-bind-indiana/e/tuck-everlasting"},
        {"title": "Wuthering Heights", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-literary-texts-into-the-unknown-indiana/e/wuthering-heights"},
    ],
    "RI.9-10": [
        {"title": '"It Is Time to Reassess Our National Priorities" by Shirley Chisholm', "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-argumentative-texts-ties-that-bind-indiana/e/it-is-time-to-reassess-our-national-priorities-by-shirley-chisholm"},
        {"title": "Born a Crime: Stories From a South African Childhood", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-crossing-the-line-indiana/e/born-a-crime-stories-from-a-south-african-childhood"},
        {"title": "Death marks the spot: The hunt for Forrest Fenn's treasure", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-informational-texts-9/e/death-marks-the-spot-the-hunt-for-forrest-fenns-treasure"},
        {"title": "Death on the ice: The mystery and tragedy of the Franklin Expedition", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/the-mystery-and-tragedy-of-the-franklin-expedition"},
        {"title": "Democracy: Stories from the Long Road to Freedom", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-thriving-indiana/e/democracy-stories-from-the-long-road-to-freedom"},
        {"title": "Exploration is exploitation: Why uncontacted tribes should be left alone", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-informational-texts-9/e/exploration-is-exploitation"},
        {"title": "How loneliness changes the way our brains process the world", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-informational-texts-9/e/how-loneliness-changes-the-way-our-brains-process-the-world"},
        {"title": "How World War I sparked the artistic movement that transformed Black America", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-informational-texts-9/e/how-wwi-sparked-the-harlem-renaissance"},
        {"title": "I Am Malala", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-nonfiction-texts-bridging-the-gap-9-indiana/e/i-am-malala"},
        {"title": "I Never Thought of It That Way", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-argumentative-texts-ties-that-bind-indiana/e/i-never-thought-of-it-that-way"},
        {"title": "Inferences (RI 9th)", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-informational-texts-9/e/inferences-9-info"},
        {"title": "Just Mercy: A Story of Justice and Redemption", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-ties-that-bind-indiana/e/just-mercy-a-story-of-justice-and-redemption"},
        {"title": "Never Caught: The Washingtons' Relentless Pursuit of Their Runaway Slave", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-crossing-the-line-indiana/e/never-caught"},
        {"title": "On Earth We're Briefly Gorgeous", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-thriving-indiana/e/on-earth-we-re-briefly-gorgeous"},
        {"title": "Parable of the Sower", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-thriving-indiana/e/parable-of-the-sower"},
        {"title": "Stamped: Racism, Antiracism, and You", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-nonfiction-texts-bridging-the-gap-9-indiana/e/stamped-racism-antiracism-and-you"},
        {"title": "Text evidence (RI)", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-informational-texts-9/e/text-evidence-9-info"},
        {"title": "The Anthropocene Reviewed", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-crossing-the-line-indiana/e/the-anthropocene-reviewed"},
        {"title": "The Immortal Life of Henrietta Lacks", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/the-immortal-life-of-henrietta-lacks"},
        {"title": "The Monsters Are Due on Maple Street", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/the-monsters-are-due-on-maple-street"},
        {"title": "The New Jim Crow", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-argumentative-texts-ties-that-bind-indiana/e/the-new-jim-crow"},
        {"title": "The Poet X", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-nonfiction-texts-bridging-the-gap-9-indiana/e/the-poet-x"},
        {"title": "The Warmth of Other Suns", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-crossing-the-line-indiana/e/the-warmth-of-other-suns"},
        {"title": "Vocabulary in context (RI)", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-informational-texts-9/e/vocabulary-in-context-9-info"},
        {"title": "When Stars Are Scattered", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-thriving-indiana/e/when-stars-are-scattered"},
        {"title": "A Long Walk to Water", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-nonfiction-texts-bridging-the-gap-9-indiana/e/a-long-walk-to-water"},
        {"title": "Braiding Sweetgrass", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/braiding-sweetgrass"},
        {"title": "Enrique's Journey", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-nonfiction-texts-bridging-the-gap-9-indiana/e/enrique-s-journey"},
        {"title": "Kindred", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-crossing-the-line-indiana/e/kindred"},
        {"title": "News of the World", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-ties-that-bind-indiana/e/news-of-the-world"},
        {"title": "Refugee", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-nonfiction-texts-bridging-the-gap-9-indiana/e/refugee"},
        {"title": "Salvage the Bones", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-ties-that-bind-indiana/e/salvage-the-bones"},
        {"title": "Say Her Name: The Life and Death of Sandra Bland", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/say-her-name-the-life-and-death-of-sandra-bland"},
        {"title": "Spare", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/spare"},
        {"title": "The Boy in the Striped Pajamas", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/the-boy-in-the-striped-pajamas"},
        {"title": "The Crucible", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-argumentative-texts-ties-that-bind-indiana/e/the-crucible"},
        {"title": "The Song of Achilles", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:thriving-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-thriving-indiana/e/the-song-of-achilles"},
        {"title": "Toni Morrison's Nobel Prize Lecture", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-crossing-the-line-indiana/e/toni-morrison-s-nobel-prize-lecture"},
        {"title": "We Are Not Free", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-crossing-the-line-indiana/e/we-are-not-free"},
        {"title": "When You Reach Me", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-ties-that-bind-indiana/e/when-you-reach-me"},
        {"title": "White Teeth", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/white-teeth"},
        {"title": "Women in Science", "url": "https://www.khanacademy.org/ela/9th-grade-reading-and-vocabulary/xd45453bfd2ae8614:key-ideas-and-details-long-passage-practice-9/xd45453bfd2ae8614:key-ideas-and-details-reading-informational-texts-9/e/women-in-science-9"},
        {"title": "Your Heart is a Muscle the Size of a Fist", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-ties-that-bind-indiana/e/your-heart-is-a-muscle-the-size-of-a-fist"},
        {"title": "Recitatif", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-ties-that-bind-indiana/e/recitatif"},
        {"title": "The Great Gatsby", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:into-the-unknown-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-into-the-unknown-indiana/e/the-great-gatsby"},
        {"title": "The Hate U Give", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:bridging-the-gap-9-indiana/x068d7167a2598a90:reading-nonfiction-texts-bridging-the-gap-9-indiana/e/the-hate-u-give"},
        {"title": "The Perfect Horse", "url": "https://www.khanacademy.org/ela/10th-grade-reading-vocab-indiana/xc7dfd10d0846d1af:ties-that-bind-long-passage-practice-indiana/xc7dfd10d0846d1af:reading-nonfiction-texts-ties-that-bind-indiana/e/the-perfect-horse"},
        {"title": "The Road", "url": "https://www.khanacademy.org/ela/9th-grade-reading-vocabulary-indiana/x068d7167a2598a90:crossing-the-line-long-passage-practice-indiana/x068d7167a2598a90:reading-nonfiction-texts-crossing-the-line-indiana/e/the-road"},
    ],
    "L.9-10": [
        {"title": "Parallel structure", "url": "https://www.khanacademy.org/humanities/grammar/syntax-conventions-of-standard-english/dangling-modifiers-and-parallel-structure/e/parallel-structure"},
        {"title": "Introduction to semicolons", "url": "https://www.khanacademy.org/humanities/grammar/punctuation-the-colon-semicolon-and-more/introduction-to-semicolons/e/introduction-to-semicolons"},
        {"title": "Using semicolons and colons", "url": "https://www.khanacademy.org/humanities/grammar/punctuation-the-colon-semicolon-and-more/introduction-to-semicolons/e/using-colons-and-semicolons"},
        {"title": "Using semicolons and commas", "url": "https://www.khanacademy.org/humanities/grammar/punctuation-the-colon-semicolon-and-more/introduction-to-semicolons/e/using-semicolons-and-commas"},
        {"title": "Introduction to colons", "url": "https://www.khanacademy.org/humanities/grammar/punctuation-the-colon-semicolon-and-more/introduction-to-colons/e/introduction-to-colons"},
    ]
}

OUTPUT_DIR = Path(__file__).parent / "output" / "ela_9_10_templates"
BLOCK_PATTERNS = ["analytics", "telemetry", "sentry", ".mp4", ".woff", "onetrust",
                  "hotjar", "doubleclick", "googletagmanager", "facebook"]


def parse_item_data(raw_json_str):
    """
    Parse itemDataAnswerless from a GraphQL response body.
    Returns dict with question_content, choices, widget_type.
    """
    try:
        data = json.loads(raw_json_str)
    except Exception:
        return None

    # itemDataAnswerless is a double-encoded JSON string
    item_data_str = None
    def find_item_data(obj):
        nonlocal item_data_str
        if isinstance(obj, dict):
            if "itemDataAnswerless" in obj and obj["itemDataAnswerless"]:
                item_data_str = obj["itemDataAnswerless"]
                return
            for v in obj.values():
                find_item_data(v)
        elif isinstance(obj, list):
            for item in obj:
                find_item_data(item)

    find_item_data(data)

    if not item_data_str:
        return None

    try:
        item = json.loads(item_data_str)
    except Exception:
        return None

    question = item.get("question", {})
    content = question.get("content", "")
    widgets = question.get("widgets", {})

    # Determine widget type and extract choices
    widget_type = "unknown"
    choices = []

    for wname, wdata in widgets.items():
        if not isinstance(wdata, dict):
            continue
        wtype = wdata.get("type", "")
        widget_type = wtype
        opts = wdata.get("options", {})

        if wtype == "radio":
            raw_choices = opts.get("choices", [])
            labels = "ABCDEFGHIJ"
            for i, c in enumerate(raw_choices):
                label = labels[i] if i < len(labels) else str(i + 1)
                choices.append({
                    "label": label,
                    "content": c.get("content", "").strip()
                })
        elif wtype == "image":
            # This is a passage item (image widget = the reading passage as rendered text)
            pass
        break  # only first widget matters

    hints = []
    for h in item.get("hints", []):
        if isinstance(h, dict):
            hints.append(h.get("content", ""))

    return {
        "question_content": content,
        "widget_type": widget_type,
        "choices": choices,
        "hints": hints,
        "raw_item": item
    }


def extract_passage_from_body(body_text):
    """Extract passage title, author, and text from page body text."""
    passage = {"title": "", "author": "", "text": ""}

    # Find "Passage" marker
    p_idx = body_text.find("\nPassage\n")
    if p_idx == -1:
        p_idx = body_text.find("Passage\n")
    if p_idx == -1:
        return passage

    passage_section = body_text[p_idx + 8:]  # skip "Passage\n"

    # Find "Question" marker to know where passage ends
    q_idx = passage_section.find("\nQuestion\n")
    if q_idx > -1:
        passage_section = passage_section[:q_idx]

    lines = [l.strip() for l in passage_section.strip().split("\n") if l.strip()]

    if not lines:
        return passage

    # First line is usually the passage title
    passage["title"] = lines[0]

    # Second line might be author ("By X" or "by X")
    if len(lines) > 1 and lines[1].lower().startswith("by "):
        passage["author"] = lines[1]
        passage["text"] = "\n".join(lines[2:])
    else:
        passage["text"] = "\n".join(lines[1:])

    return passage


async def scrape_exercise(page, exercise_info, standard):
    """
    Scrape a single exercise page.
    Returns dict with passage + question(s) or None on failure.
    """
    url = exercise_info["url"]
    title = exercise_info["title"]
    slug = url.rstrip("/").split("/e/")[-1]

    # Check if already done
    out_path = OUTPUT_DIR / f"{slug}.json"
    if out_path.exists():
        print(f"  SKIP (exists): {title}", flush=True)
        return json.loads(out_path.read_text())

    print(f"  Scraping: {title} ...", flush=True)

    passage_raw = None
    question_raw = None
    exercise_length = 0

    async def on_response(response):
        nonlocal passage_raw, question_raw, exercise_length
        resp_url = response.url
        try:
            if "getAssessmentItemById" in resp_url and passage_raw is None:
                body = await response.text()
                data = json.loads(body)
                item = (data.get("data", {})
                            .get("assessmentItemById", {})
                            .get("item"))
                if item and item.get("itemDataAnswerless"):
                    passage_raw = json.loads(item["itemDataAnswerless"])

            elif "getInitialDataForPrePhantomUser" in resp_url and question_raw is None:
                body = await response.text()
                data = json.loads(body)
                item = (data.get("data", {})
                            .get("assessmentItem", {})
                            .get("item"))
                if item and item.get("itemDataAnswerless"):
                    question_raw = json.loads(item["itemDataAnswerless"])
                # Also grab exercise length
                try:
                    task = (data["data"]
                            ["getDummyPracticeTaskForPrePhantomUser"]
                            ["userTask"]["task"])
                    exercise_length = task.get("exerciseLength", 4)
                except Exception:
                    exercise_length = 4
        except Exception:
            pass

    page.on("response", on_response)

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"    ERROR loading: {e}", flush=True)
        page.remove_listener("response", on_response)
        return None

    await asyncio.sleep(10)  # longer wait for slower course pages
    page.remove_listener("response", on_response)

    # --- Parse passage ---
    passage = {"title": "", "author": "", "text": ""}
    if passage_raw:
        content = passage_raw.get("question", {}).get("content", "")
        # Remove leading image widget placeholder(s)
        content = re.sub(r"^\s*\[\[☃ image \d+\]\]\s*", "", content).strip()
        # Extract ## title heading
        title_match = re.match(r"^##(.+)", content, re.MULTILINE)
        if title_match:
            passage["title"] = title_match.group(1).strip()
            content = content[title_match.end():].strip()
        # Extract *author* line (italic)
        author_match = re.match(r"^\*([^\*]+)\*", content)
        if author_match:
            passage["author"] = author_match.group(1).strip()
            content = content[author_match.end():].strip()
        # Clean up all widget references: [[☃ definition N]] -> keep as [word]
        content = re.sub(r"\[\[☃ definition \d+\]\]", "[word]", content)
        # Clean up any remaining widget placeholders
        content = re.sub(r"\[\[☃ \w+ \d+\]\]", "", content)
        passage["text"] = content.strip()
    else:
        # Fallback: extract from page body text
        body_text = await page.inner_text("body")
        passage = extract_passage_from_body(body_text)

    # --- Parse question ---
    questions = []
    if question_raw:
        q = question_raw.get("question", {})
        content = q.get("content", "").strip()
        widgets = q.get("widgets", {})

        widget_type = "unknown"
        choices = []
        for wname, wdata in widgets.items():
            if not isinstance(wdata, dict):
                continue
            wtype = wdata.get("type", "")
            widget_type = wtype
            opts = wdata.get("options", {})
            if wtype == "radio":
                labels = "ABCDEFGHIJ"
                for i, c in enumerate(opts.get("choices", [])):
                    choices.append({
                        "label": labels[i] if i < len(labels) else str(i+1),
                        "content": c.get("content", "").strip()
                    })
            break

        # Clean up widget placeholder in question content
        content = re.sub(r"\[\[☃ \w+ \d+\]\]", "", content).strip()

        hints = [h.get("content", "") for h in question_raw.get("hints", [])
                 if isinstance(h, dict)]

        if content:
            questions.append({
                "question_content": content,
                "widget_type": widget_type,
                "choices": choices,
                "hints": hints
            })

    print(f"    -> passage: {len(passage['text'])} chars, "
          f"questions: {len(questions)}/{exercise_length}", flush=True)

    result = {
        "title": title,
        "url": url,
        "slug": slug,
        "ccss_standard": standard,
        "exercise_length": exercise_length,
        "passage": passage,
        "questions": questions,
        "note": f"KA serves 1/{exercise_length} questions to anonymous users. "
                f"Passage and sample question captured for skeleton generation."
    }

    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = sum(len(v) for v in EXERCISES.values())
    print(f"Scraping {total} exercises across {len(EXERCISES)} standards...", flush=True)

    all_results = {}
    done = 0
    failed = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
        ctx = await browser.new_context(ignore_https_errors=True)
        page = await ctx.new_page()

        async def block(route):
            if any(x in route.request.url for x in BLOCK_PATTERNS):
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block)
        page.on("pageerror", lambda e: None)
        page.on("console", lambda m: None)

        for standard, exercises in EXERCISES.items():
            print(f"\n=== {standard} ({len(exercises)} exercises) ===", flush=True)
            all_results[standard] = []

            for ex in exercises:
                result = await scrape_exercise(page, ex, standard)
                if result:
                    all_results[standard].append(result)
                    done += 1
                else:
                    failed.append(ex["title"])
                await asyncio.sleep(1)

        await browser.close()

    # Summary
    print(f"\n{'='*50}")
    print(f"Done: {done}/{total} exercises scraped")
    if failed:
        print(f"Failed ({len(failed)}): {failed}")

    # Save master index
    index_path = OUTPUT_DIR / "index.json"
    index_path.write_text(json.dumps({
        std: [{"title": r["title"], "slug": r["slug"],
               "questions": len(r["questions"]),
               "passage_chars": len(r["passage"]["text"])}
              for r in results]
        for std, results in all_results.items()
    }, indent=2))
    print(f"Index saved to {index_path}")


if __name__ == "__main__":
    asyncio.run(main())
