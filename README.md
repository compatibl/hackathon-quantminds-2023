# QuantMinds Hackathon (2023)
![GitHub](https://img.shields.io/github/license/compatibl/hackathon)
![PyPI - Downloads](https://img.shields.io/pypi/dm/hackathon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hackathon)
![PyPI](https://img.shields.io/pypi/v/hackathon)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/compatibl/hackathon/pulls)
## Overview

The theme of this inaugural QuantMinds Hackathon is Quantitative Finance AI.

**QuantMinds conference pass is not required and participation is possible with or without coding.**

- Entering the hackathon requires physical presence at the QuantMinds
conference venue during registration (in case of a team entry, by at least one team member).
- During the hackathon, participants can work onsite or offsite. Limited space will be available at the venue 
on a first come, first served basis.
- Register in advance by visiting [this link](https://informaconnect.com/quantminds-international/hackathon/)
or on-site at the start of the hackathon (time and venue details are provided below).

This package provides guidelines and competition rules. The source
code samples will be pushed to GitHub prior to competition start.

## Venue and Date

The Hackathon will take place on Monday, November 13, from 9am to 4pm London time at
the InterContinental O2 Hotel, One Waterview Drive, Greenwich Peninsula, SE10 0TW, London.

## Entries

- Both individual and team participation is permitted (one entry per individual)
- Each individual or team can participate in one or more of the four categories

## Equipment

- Participants will use their own computer equipment. 
- Instructions for registering and getting API keys for online model hosting services will be provided.
- The cost of model hosting service use during the hackathon is expected to be less than GBP 50.

## Competition Categories

This year the competition will be held in two streams, with each stream
further subdivided by model type (GPT or LLAMA) for the total of four categories.

1. Pricing Model Source Code Comprehension Stream (Source-GPT and Source-LLAMA categories)
2. Trade Confirmation Comprehension Stream (Text-GPT and Text-LLAMA categories)

## Scoring Rules

- At the beginning of the hackathon, examples for each category will be randomly divided into two 
equal parts through a public drawing.
- Participants will receive the first half of the examples to develop their competition entries.
- When the hackathon concludes, the second half of the examples will be utilized to score the entries.

## Submission Format

Participants can choose between non-code and code submission formats in each of the four categories,
to be scored together in each category.

### Non-Code Submission Format

- The competition entry is a text prompt submitted by email
guides the model to produce the desired
output in JSON format.
- The prompt can be developed using any chat application or playground.
- An official playground
application will be provided by the organizers for use with participants' own keys.
- The entry is scored by parsing JSON in the model output.
- Any text before the opening or after the closing curly brackets is ignored.

### Code Submission Format

- Participants can submit their own Python code via GitHub.
- The code should read a .csv file with input data and produce a .csv file with
output fields.
- A sample open-source environment will be provided by the organizers in this package, however
its use is not required and any other open-source environment in Python or another mainstream
programming language that the organizers can install and run for scoring can be used.

## Scoring Rules

- For each sample, the model output must provide category (multiple choice) and parameters.
- Incorrectly identifying the category among the available choices leads to zero score for the sample.
- For each sample where category is identified correctly, score is the number of correctly identified parameter values
including for those parameters whose correct value is empty.
- For code submissions, the output must comply with the .csv format provided. Any additional text will be disregarded.
- For non-code submissions, the data will be extracted from JSON in the model output. Any text outside JSON will be
disregarded. Any additional fields in JSON will be disregarded. If more than one JSON is provided in the output,
only the first one will be used.

## Models

- When using GPT models, either GPT-4 or GPT-3.4-Turbo models are permitted. GPT-4-Turbo
model is not permitted.
- When using LLAMA models, any model from the LLAMA 2 family is permitted, including
LLAMA-2-70B and CodeLlama-34B.

*IMPORTANT:* The use of ChatGPT (as opposed to OpenAI API) 
is not recommended as ChatGPT has very different behavior than the
[OpenAI API](https://platform.openai.com/overview), and the model
will be scored using the OpenAI API rather than ChatGPT.

- Both on-code and code submissions will be scored using model hosting service specified by the participant.
- Only those hosting services for which the organizers can obtain a key online without a lengthy
submission process are permitted (e.g. OpenAI, Replicate, or Fireworks.ai). The cost of scoring runs
will be borne by the organizers.
- Model settings such as seed, temperature, top-p, top-k and others may be specified with the entry.
