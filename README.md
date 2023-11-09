# QuantMinds-CompatibL Hackathon (2023)
![GitHub](https://img.shields.io/github/license/compatibl/hackathon)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/compatibl/hackathon/pulls)
## Overview

The theme of the inaugural QuantMinds-CompatibL Hackathon is Quantitative Finance AI.

**QuantMinds conference pass is not required and participation is possible with or without coding.**

- Entering the hackathon requires physical presence at the QuantMinds
conference venue during registration (in case of a team entry, by at least one team member).
- During the hackathon, participants can work onsite or offsite. Limited space will be available at the venue 
on a first come, first served basis.
- Register in advance by emailing [Martina.DeGrassi@informa.com](mailto:Martina.DeGrassi@informa.com)
or on-site at the start of the hackathon (time and venue details are provided below).

This package provides guidelines and competition rules. The source
code samples will be pushed to GitHub prior to competition start.

## Technical Support

For technical support before and during the hackathon, email
[support@compatibl-hackathon.freshdesk.com](mailto:support@compatibl-hackathon.freshdesk.com)

## Date and Venue

The Hackathon will take place on Monday, November 13, from 9am to 4pm London time at
the InterContinental London - The O2, 1 Waterview Drive, SE10 0TW, London. The hotel is located
on Greenwich Peninsula near the O2 Arena
([Google Maps](https://maps.app.goo.gl/bRSPhmtevTKvqy6x8)).

Further venue and event details can be found [here](https://informaconnect.com/quantminds-international/hackathon/).

## Competition

- Both individual and team participation is permitted (one entry per individual)
- Each individual or team can participate in one or more of the four categories
- Participants can provide an alias to be shown in scoreboard for individual and team entries.
Real names will not be disclosed without permission. 

Most importantly, participation in the hackathon without entering the competition is welcome and
can provide valuable experience with practical applications of AI in a collaborative environment.

## Equipment

- With models hosted online, a basic laptop is all you need.
- For non-coding entries, you can use an online playground provided by the organizers or any other
playground (however see the note below about third-party playgrounds).
- For coding entries, you can clone this GitHub repo and work using Python 3.9 or later, or use your own tools.
- Instructions for registering and getting API keys for online model hosting services will be provided.
- The cost of model hosting service use during the hackathon is expected to be less than GBP 50.

## Scoring Software Package

- The open-source software package that will be used for scoring can be downloaded from GitHub at this URL
.
- The same package will be available online during the hackathon at the URL that will be posted at the start
of the competition.
- The same package can be used to develop and test your entry for both coding and non-coding submissions.
Its use is not required and is a matter of convenience. Any other playground or Python package can be used
instead to submit the entry.

#### Installation

1. Ensure your computer has Python 3.9 or later
2. Checkout from GitHub:
[https://github.com/compatibl/hackathon-quantminds-2023](https://github.com/compatibl/hackathon-quantminds-2023)
3. Create and activate venv or conda environment
4. Run `pip install -r requirements.txt`
5. Run `python -m hackathon`
6. Click on the URL in text output to open the UI

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

- Non-coding and coding entries will compete alongside one another in each category.
- Coding participants are welcome to use and modify pre- and post-processing code
for the non-coding  entries included in this GitHub repo.
- Using advanced methods including chains is permitted for coding entries.
- Using your own tools instead of cloning this repo is permitted as long as both
the entry itself and the tools are licensed under Apache or MIT license.
Contact the organizers for information on other licenses.

Participants can choose between non-code and code submission formats in each of the four categories,
to be scored together in each category.

#### Non-Code Submission Format Details

- The competition entry is a text prompt submitted by email
guides the model to produce the desired
output in JSON format.
- The prompt can be developed using any chat application or playground.
- An official playground
application will be provided by the organizers for use with participants' own keys.
- The entry is scored by parsing JSON in the model output.
- Any text before the opening or after the closing curly brackets is ignored.

#### Code Submission Format Details

- Participants can submit their own Python code via GitHub.
- The code should read a .csv file with input data and produce a .csv file with
output fields.
- A sample open-source environment will be provided by the organizers in this package, however
its use is optional and the entry can use any other open-source toolset in Python (MIT or Apache license).
- The competition entry itself must be provided under an open source license (MIT or Apache)
as keeping the entries confidential is not practical in competition format.

## Scoring Rules

- For each sample, the model output must provide category (multiple choice) and parameters.
- Incorrectly identifying the category among the available choices leads to zero score for the sample.
- For each sample where category is identified correctly, score is the number of correctly identified parameter values
including for those parameters whose correct value is empty.
- For code submissions, the output must comply with the .csv format provided. Any additional text will be disregarded.
- For non-code submissions, the data will be extracted from JSON in the model output. Any text outside JSON will be
disregarded. Any additional fields in JSON will be disregarded. If more than one JSON is provided in the output,
only the first one will be used.

## Model Versions

- When using GPT models, either GPT-4 or GPT-3.4-Turbo models are permitted. GPT-4-Turbo
model is not permitted.
- When using LLAMA models, any model from the LLAMA 2 family is permitted, including
LLAMA-2-70B and CodeLlama-34B.
- Model settings such as seed, temperature, top-p, top-k and others may be specified with the entry.

## Use of ChatGPT and Third-Party Playgrounds

- Using ChatGPT to prepare a submission is not recommended. Reason: ChatGPT and OpenAI API have significant differences, 
which will likely cause reduced performance when the entry is tuned using ChatGPT and then scored using OpenAI API. 
- Similar differences may exist between some of the LLAMA-based third party playgrounds and the LLAMA 2 API.
- When using a third-party playground, ensure that no hidden pre- or post-processing is present and
the model parameters are known and can be specified with your competition entry.

## Model Hosting

- Both on-code and code submissions will be scored using model hosting service specified by the participant.
- For non-coding entries, the options are OpenAI (GPT categories only), Replicate, or Fireworks.ai.
- For coding entries, the same options are available or any other where
the organizers can obtain a key online without a lengthy submission process.
- Coding entries can also use local models. The organizers will provide GPU hardware to score them.
- The cost of scoring using hosted models or GPU hardware will be borne by the organizers.

